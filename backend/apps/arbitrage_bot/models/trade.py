# backend/arbitrage_bot/models/trade.py
from django.db import models
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from django.utils import timezone

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

# Django ORM model for persistent trades (used by RiskManager.record_trade)
class TradeRecord(models.Model):
    triangle = models.JSONField(default=list)                # store ['BTC/USDT','ETH/BTC','ETH/USDT']
    entry_amount = models.FloatField()
    exit_amount = models.FloatField()
    profit = models.FloatField()
    profit_percentage = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=32, default='executed')
    exchange = models.CharField(max_length=64, default='unknown')
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'arbitrage_trade'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Trade {self.id if hasattr(self, 'id') else self.pk} | {self.exchange} | {self.profit:+.4f}$"