# backend/arbitrage_bot/core/risk_manager.py
import logging
import os
from typing import Dict, List, Any
from datetime import datetime
import time
from django.utils import timezone
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_position_size: float = 100, max_daily_loss: float = 50, max_drawdown: float = 20):
        # Load base balance from env; fall back to default if not set
        base_balance_env = os.getenv('BASE_BALANCE')
        try:
            base_balance = float(base_balance_env) if base_balance_env is not None else 1000.0
        except Exception:
            base_balance = 1000.0
            logger.warning("Invalid BASE_BALANCE env value, using default 1000.0")

        # Minimum trade size (respect environment or default to $10)
        try:
            self.min_trade_amount = float(os.getenv('MIN_TRADE_AMOUNT', 10.0))
        except Exception:
            self.min_trade_amount = 10.0

        # Conservative limits for real trading
        # Ensure max_position_size is not smaller than the configured minimum trade amount
        if max_position_size < self.min_trade_amount:
            logger.info(f"Configured max_position_size (${max_position_size}) is below min trade amount (${self.min_trade_amount}); raising to min trade amount.")
            max_position_size = self.min_trade_amount

        self.max_position_size = max_position_size  # $ max per trade
        self.max_daily_loss = max_daily_loss        # $ max daily loss
        self.max_drawdown = max_drawdown            # % max drawdown from peak

        # Tracking metrics
        self.daily_trades: List[Dict[str, Any]] = []
        self.daily_pnl: float = 0.0
        self.total_trades: int = 0
        self.total_profit: float = 0.0
        self.successful_trades: int = 0
        # Initialize balances from BASE_BALANCE
        self.peak_balance: float = base_balance
        self.current_balance: float = base_balance

        # Trade history for cooldowns / statistics
        self.trade_history: List[Dict[str, Any]] = []

        # Diagnostics
        self.last_rejection_reason: str = ""
        self.rejection_count: int = 0

    # Backwards-compatible wrapper used by existing code
    def can_execute_trade(self, opportunity, proposed_size: float) -> bool:
        """
        Backwards-compatible check used in older call-sites.
        Accepts an 'opportunity' object/dict with 'profit_percentage' or a numeric profit %.
        Returns boolean (old behaviour).
        """
        try:
            profit_pct = 0.0
            if isinstance(opportunity, dict):
                profit_pct = float(opportunity.get('profit_percentage', 0.0))
            elif hasattr(opportunity, 'profit_percentage'):
                profit_pct = float(getattr(opportunity, 'profit_percentage', 0.0))
            elif isinstance(opportunity, (int, float)):
                profit_pct = float(opportunity)
            approved, _ = self.can_execute_trade_real([], proposed_size, expected_profit=proposed_size * (profit_pct/100.0), profit_percentage=profit_pct)
            return approved
        except Exception as e:
            logger.error(f"Error in legacy can_execute_trade wrapper: {e}")
            return False

    def can_execute_trade_real(self, triangle: List[str], proposed_size: float, 
                               expected_profit: float, profit_percentage: float) -> tuple[bool, str]:
        """Enhanced risk check for real trading.

        Returns (approved: bool, reason: str)
        """
        # 0. Sanity on proposed_size
        try:
            proposed_size = float(proposed_size)
        except Exception:
            reason = "Invalid trade size"
            logger.debug(f"[RiskCheck] {reason}: {proposed_size}")
            self.last_rejection_reason = reason
            self.rejection_count += 1
            return False, reason

        # 1. Minimum trade amount
        if proposed_size < self.min_trade_amount:
            reason = f"Trade size ${proposed_size:.2f} below minimum allowed ${self.min_trade_amount:.2f}"
            logger.info(f"Trade rejected by risk manager: {reason}")
            self.last_rejection_reason = reason
            self.rejection_count += 1
            return False, reason

        # 2. Position size limit
        if proposed_size > self.max_position_size:
            reason = f"Trade size ${proposed_size:.2f} exceeds maximum ${self.max_position_size:.2f}"
            logger.info(f"Trade rejected by risk manager: {reason}")
            self.last_rejection_reason = reason
            self.rejection_count += 1
            return False, reason
        
        # 3. Daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            reason = f"Daily loss limit reached: ${self.daily_pnl:.2f}"
            logger.info(f"Trade rejected by risk manager: {reason}")
            self.last_rejection_reason = reason
            self.rejection_count += 1
            return False, reason
        
        # 4. Drawdown limit
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - self.current_balance) / self.peak_balance * 100.0
            if drawdown >= self.max_drawdown:
                reason = f"Max drawdown reached: {drawdown:.1f}%"
                logger.info(f"Trade rejected by risk manager: {reason}")
                self.last_rejection_reason = reason
                self.rejection_count += 1
                return False, reason
        
        # 5. Effective profit threshold - use configured minimum from DB if available
        try:
            # lazy import to avoid circular imports
            from ..models.trade import BotConfig  # type: ignore
            cfg, _ = BotConfig.objects.get_or_create(pk=1)
            min_profit_threshold = getattr(cfg, "min_profit_threshold", 0.3)
        except Exception:
            min_profit_threshold = 0.3

        fee_estimate = Decimal('0.2')  # percent
        try:
            # Convert profit_percentage safely to Decimal
            p_pct = Decimal(str(profit_percentage or 0.0))
        except (InvalidOperation, TypeError):
            p_pct = Decimal('0.0')

        # Compute effective profit and quantize for stability (6 decimal places)
        effective_profit = (p_pct - fee_estimate).quantize(Decimal('0.000001'))

        # Ensure threshold is Decimal for comparison
        try:
            threshold_dec = Decimal(str(min_profit_threshold))
        except (InvalidOperation, TypeError):
            threshold_dec = Decimal('0.3')

        # DEBUG logging
        logger.debug(
            f"[RiskCheck] raw_profit={float(p_pct):.6f}%, "
            f"fee_estimate={float(fee_estimate):.2f}%, "
            f"effective_profit={float(effective_profit):.6f}%, "
            f"threshold={float(threshold_dec):.6f}%"
        )

        if effective_profit < threshold_dec:
            reason = f"Insufficient profit after estimated fees: {float(effective_profit):.2f}% (need {float(threshold_dec):.2f}%)"
            logger.info(f"Trade rejected by risk manager: {reason}")
            self.last_rejection_reason = reason
            self.rejection_count += 1
            return False, reason
        
        # 6. Consecutive losses cooldown
        recent_trades = self.trade_history[-5:] if self.trade_history else []
        if len(recent_trades) >= 3:
            losses = sum(1 for t in recent_trades if t.get('profit', 0.0) < 0)
            if losses >= 3:
                reason = "Too many recent losses - cooling off period"
                logger.info(f"Trade rejected by risk manager: {reason}")
                self.last_rejection_reason = reason
                self.rejection_count += 1
                return False, reason
        
        # 7. Minimum spacing between trades
        if self.trade_history:
            last_trade_time = self.trade_history[-1].get('timestamp', None)
            if last_trade_time and (time.time() - last_trade_time < 10):  # seconds
                reason = "Trading too frequently - please wait before submitting another trade"
                logger.info(f"Trade rejected by risk manager: {reason}")
                self.last_rejection_reason = reason
                self.rejection_count += 1
                return False, reason
        
        # 8. Basic sanity: expected_profit should be > 0.0
        try:
            if float(expected_profit) <= 0:
                reason = "Expected profit non-positive"
                logger.info(f"Trade rejected by risk manager: {reason}")
                self.last_rejection_reason = reason
                self.rejection_count += 1
                return False, reason
        except Exception:
            reason = "Expected profit invalid"
            logger.info(f"Trade rejected by risk manager: {reason}")
            self.last_rejection_reason = reason
            self.rejection_count += 1
            return False, reason

        # Approved
        logger.debug(f"Trade approved by risk manager: size=${proposed_size:.2f}, effective_profit={float(effective_profit):.6f}%, threshold={float(threshold_dec):.6f}%")
        self.last_rejection_reason = ""
        return True, "Trade approved"
    
    def record_trade(self, trade_size: float, profit: float, triangle: List[str] = None, exchange: str = 'unknown', status: str = 'executed'):
        """Record trade with enhanced tracking and persist to DB"""
        ts = time.time()
        profit_pct = (profit / trade_size) * 100.0 if trade_size else 0.0
        trade_record = {
            'timestamp': ts,
            'size': trade_size,
            'profit': profit,
            'profit_percentage': profit_pct,
            'triangle': triangle or [],
            'exchange': exchange,
            'status': status
        }

        # In-memory tracking
        self.daily_trades.append(trade_record)
        self.trade_history.append(trade_record)
        self.daily_pnl += profit
        self.total_profit += profit
        self.total_trades += 1

        # Update balances & peak
        self.current_balance += profit
        self.peak_balance = max(self.peak_balance, self.current_balance)

        if profit > 0:
            self.successful_trades += 1

        logger.info(f"Trade recorded: Size=${trade_size:.2f}, Profit=${profit:.4f}, Daily PnL=${self.daily_pnl:.2f}")

        # Persist to DB (best-effort: fail silently to avoid breaking runtime)
        try:
            # Lazy import to avoid module import cycles
            from ..models.trade import TradeRecord  # type: ignore
            TradeRecord.objects.create(
                triangle=trade_record['triangle'],
                entry_amount=trade_size,
                exit_amount=trade_size + profit,
                profit=profit,
                profit_percentage=profit_pct,
                timestamp=timezone.now(),
                status=status,
                exchange=exchange
            )
            logger.debug("Trade persisted to DB (TradeRecord)")
        except Exception as e:
            logger.warning(f"Could not persist trade to DB: {e}")

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate (%)"""
        if self.total_trades == 0:
            return 0.0
        return (self.successful_trades / self.total_trades) * 100.0
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Return comprehensive risk metrics for UI / APIs"""
        drawdown = ((self.peak_balance - self.current_balance) / self.peak_balance * 100.0) if self.peak_balance > 0 else 0.0
        return {
            'current_balance': round(self.current_balance, 4),
            'peak_balance': round(self.peak_balance, 4),
            'drawdown_percentage': round(drawdown, 4),
            'daily_pnl': round(self.daily_pnl, 4),
            'total_trades': self.total_trades,
            'success_rate': round(self.success_rate, 2),
            'total_profit': round(self.total_profit, 4),
            'daily_trades_count': len(self.daily_trades),
            'max_daily_loss_remaining': round(self.max_daily_loss + min(0, self.daily_pnl), 4),
            'risk_limits': {
                'max_position_size': self.max_position_size,
                'min_trade_amount': self.min_trade_amount,
                'max_daily_loss': self.max_daily_loss,
                'max_drawdown': self.max_drawdown
            },
            'last_rejection_reason': self.last_rejection_reason,
            'rejection_count': self.rejection_count
        }
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call this daily)"""
        self.daily_trades = []
        self.daily_pnl = 0.0
        logger.info("Daily metrics reset")
    
    def update_risk_limits(self, max_position_size: float = None, max_daily_loss: float = None, max_drawdown: float = None):
        """Update risk limits dynamically"""
        if max_position_size is not None:
            # Respect min trade amount when updating
            try:
                mps = float(max_position_size)
                if mps < self.min_trade_amount:
                    logger.info(f"Attempted to set max_position_size=${mps}, below min_trade_amount=${self.min_trade_amount}. Clamping to min_trade_amount.")
                    mps = self.min_trade_amount
                self.max_position_size = mps
            except Exception:
                logger.warning("Invalid max_position_size provided")
        if max_daily_loss is not None:
            self.max_daily_loss = max_daily_loss
        if max_drawdown is not None:
            self.max_drawdown = max_drawdown
        
        logger.info(f"Risk limits updated: Position=${self.max_position_size}, DailyLoss=${self.max_daily_loss}, Drawdown={self.max_drawdown}%")