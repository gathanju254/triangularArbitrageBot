# backend/apps/arbitrage_bot/models/__init__.py
from .arbitrage_opportunity import ArbitrageOpportunity, ArbitrageOpportunityRecord
from .trade import Trade, TradeRecord

__all__ = [
    'ArbitrageOpportunity', 
    'ArbitrageOpportunityRecord',
    'Trade', 
    'TradeRecord', 
]