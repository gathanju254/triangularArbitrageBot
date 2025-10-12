# backend/arbitrage_bot/core/risk_manager.py
import logging
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_position_size: float = 1000, max_daily_loss: float = 100):
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.daily_trades = []
        self.daily_pnl = 0.0
        
    def can_execute_trade(self, opportunity, proposed_size: float) -> bool:
        """Check if trade meets risk criteria"""
        # Check position size
        if proposed_size > self.max_position_size:
            logger.warning(f"Trade size {proposed_size} exceeds maximum {self.max_position_size}")
            return False
        
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            logger.warning(f"Daily loss limit reached: {self.daily_pnl}")
            return False
        
        # Check opportunity quality
        if opportunity.profit_percentage < 0.1:  # Minimum profit threshold
            return False
            
        return True
    
    def record_trade(self, trade_size: float, profit: float):
        """Record trade for risk tracking"""
        self.daily_trades.append({
            'timestamp': datetime.now(),
            'size': trade_size,
            'profit': profit
        })
        self.daily_pnl += profit
        
    def reset_daily_metrics(self):
        """Reset daily metrics (call this daily)"""
        self.daily_trades = []
        self.daily_pnl = 0.0