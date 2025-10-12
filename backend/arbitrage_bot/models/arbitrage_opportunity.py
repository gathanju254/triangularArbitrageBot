# backend/arbitrage_bot/models/arbitrage_opportunity.py
from dataclasses import dataclass
from typing import Dict, List
import numpy as np

@dataclass
class ArbitrageOpportunity:
    triangle: List[str]
    profit_percentage: float
    timestamp: np.datetime64
    prices: Dict[str, float]
    
    def __post_init__(self):
        if not isinstance(self.triangle, list) or len(self.triangle) != 3:
            raise ValueError("Triangle must be a list of 3 currency pairs")