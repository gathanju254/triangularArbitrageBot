# backend/arbitrage_bot/core/order_execution.py
import logging
from typing import Dict, List
from ..models.trade import Trade
from ..exchanges.binance import BinanceClient
from ..exchanges.kraken import KrakenClient
from .risk_manager import RiskManager
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self):
        self.exchanges = {
            'binance': BinanceClient(),
            'kraken': KrakenClient()
        }
        self.risk_manager = RiskManager()
        self.active_trades = {}
    
    def execute_triangle(self, triangle: List[str], prices: Dict[str, float], amount: float) -> Trade:
        """Execute a triangular arbitrage trade"""
        trade_id = str(uuid.uuid4())
        
        try:
            # Check risk management
            if not self.risk_manager.can_execute_trade(triangle, amount):
                raise Exception("Trade rejected by risk manager")
            
            # Calculate expected profit
            initial_amount = amount
            step1 = initial_amount * prices[triangle[0]]
            step2 = step1 * prices[triangle[1]]
            final_amount = step2 * prices[triangle[2]]
            expected_profit = final_amount - initial_amount
            
            # For demo purposes, we'll simulate execution
            # In production, you would execute real orders here
            logger.info(f"Executing triangle: {triangle} with amount: {amount}")
            
            # Simulate trade execution
            trade = Trade(
                id=trade_id,
                triangle=triangle,
                entry_amount=initial_amount,
                exit_amount=final_amount,
                profit=expected_profit,
                profit_percentage=(expected_profit / initial_amount) * 100,
                timestamp=datetime.now(),
                status='executed',
                exchange='binance'  # Default exchange for demo
            )
            
            # Record trade in risk manager
            self.risk_manager.record_trade(amount, expected_profit)
            
            logger.info(f"Trade executed successfully: {trade_id}, Profit: {expected_profit:.4f}")
            return trade
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            trade = Trade(
                id=trade_id,
                triangle=triangle,
                entry_amount=amount,
                exit_amount=amount,  # No change on failure
                profit=0,
                profit_percentage=0,
                timestamp=datetime.now(),
                status='failed',
                exchange='binance',
                error_message=str(e)
            )
            return trade
    
    def get_trade_status(self, trade_id: str) -> Dict:
        """Get status of a specific trade"""
        return self.active_trades.get(trade_id, {})