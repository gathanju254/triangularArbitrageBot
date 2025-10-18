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

# Bot configuration persisted in DB (single-row config)
class BotConfig(models.Model):
    # Trading Configuration
    base_balance = models.FloatField(default=1000.0)
    max_position_size = models.FloatField(default=100.0)
    max_daily_loss = models.FloatField(default=50.0)
    max_drawdown = models.FloatField(default=20.0)
    min_profit_threshold = models.FloatField(default=0.3)  # percent
    
    # Trade size configuration
    trade_size_fraction = models.FloatField(default=0.01)  # 1% of base balance
    
    # New fields from Settings.jsx
    slippage_tolerance = models.FloatField(default=0.1)  # percent
    auto_restart = models.BooleanField(default=True)
    
    # Trading mode
    trading_enabled = models.BooleanField(default=False)
    
    # Enabled exchanges (store as JSON array)
    enabled_exchanges = models.JSONField(default=list)

    class Meta:
        db_table = 'bot_config'

    def __str__(self):
        return f"BotConfig(pk={self.pk})"

    @property
    def enabled_exchanges_list(self):
        """Get enabled exchanges as list"""
        if isinstance(self.enabled_exchanges, list):
            return self.enabled_exchanges
        return ['binance']  # default

    @enabled_exchanges_list.setter
    def enabled_exchanges_list(self, value):
        """Set enabled exchanges from list"""
        if isinstance(value, list):
            self.enabled_exchanges = value