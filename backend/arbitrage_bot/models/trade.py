# backend/arbitrage_bot/models/trade.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Trade:
    id: str
    triangle: list
    entry_amount: float
    exit_amount: float
    profit: float
    profit_percentage: float
    timestamp: datetime
    status: str  # 'executed', 'failed', 'pending'
    exchange: str
    error_message: Optional[str] = None