# backend/arbitrage_bot/models/arbitrage_opportunity.py
from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np
from django.db import models
from django.utils import timezone

@dataclass
class ArbitrageOpportunity:
    triangle: List[str]
    profit_percentage: float
    timestamp: np.datetime64
    prices: Dict[str, float]
    steps: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.triangle, list) or len(self.triangle) != 3:
            raise ValueError("Triangle must be a list of 3 currency pairs")

# Persisted model so admin can show historical opportunities
class ArbitrageOpportunityRecord(models.Model):
    triangle = models.JSONField(default=list)       # e.g. ['BTC/USDT','ETH/BTC','ETH/USDT']
    profit_percentage = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    prices = models.JSONField(default=dict)
    steps = models.JSONField(default=list)
    source = models.CharField(max_length=32, default='live')  # 'live' | 'demo' | 'sample'

    class Meta:
        db_table = 'arbitrage_opportunity'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Opportunity {self.pk} | {self.profit_percentage:.4f}% | {self.timestamp.isoformat()}"