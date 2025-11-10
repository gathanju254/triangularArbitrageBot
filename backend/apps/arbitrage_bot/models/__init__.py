# backend/apps/arbitrage_bot/models/__init__.py
from .arbitrage_opportunity import ArbitrageOpportunity, ArbitrageOpportunityRecord
from .trade import Trade, TradeRecord

# Import RiskAlert if it exists
try:
    from .risk_alert import RiskAlert
    __all__ = [
        'ArbitrageOpportunity', 
        'ArbitrageOpportunityRecord',
        'Trade', 
        'TradeRecord', 
        'BotConfig',
        'RiskAlert'
    ]
except ImportError:
    __all__ = [
        'ArbitrageOpportunity', 
        'ArbitrageOpportunityRecord',
        'Trade', 
        'TradeRecord', 
    ]