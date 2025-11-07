# backend/arbitrage_bot/tasks.py
import logging
from celery import Celery
from .core.arbitrage_engine import ArbitrageEngine
from .core.market_data import MarketDataManager
from .core.order_execution import OrderExecutor

logger = logging.getLogger(__name__)

# Celery app
app = Celery('arbitrage_tasks')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Global instances
arbitrage_engine = ArbitrageEngine()
market_data_manager = MarketDataManager()
order_executor = OrderExecutor()

@app.task
def scan_arbitrage_opportunities():
    """Celery task to continuously scan for arbitrage opportunities"""
    try:
        prices = market_data_manager.prices
        opportunities = arbitrage_engine.scan_opportunities(prices)
        
        # Log opportunities
        for opp in opportunities:
            logger.info(f"Arbitrage opportunity found: {opp.triangle} - Profit: {opp.profit_percentage:.4f}%")
        
        return {
            'opportunities_found': len(opportunities),
            'opportunities': [
                {
                    'triangle': opp.triangle,
                    'profit_percentage': opp.profit_percentage
                } for opp in opportunities
            ]
        }
    except Exception as e:
        logger.error(f"Error in arbitrage scan: {e}")
        return {'error': str(e)}

@app.task
def execute_arbitrage_trade(triangle: list, amount: float):
    """Execute an arbitrage trade"""
    try:
        prices = market_data_manager.prices
        trade = order_executor.execute_triangle(triangle, prices, amount)
        return {
            'trade_id': trade.id,
            'status': trade.status,
            'profit': trade.profit,
            'error': trade.error_message
        }
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return {'error': str(e)}