# backend/arbitrage_bot/core/arbitrage_engine.py
import logging
import numpy as np
from typing import List, Dict, Optional
from ..models.arbitrage_opportunity import ArbitrageOpportunity
from ..utils.helpers import calculate_profit_percentage

logger = logging.getLogger(__name__)

class ArbitrageEngine:
    def __init__(self, min_profit_threshold: float = 0.2):
        self.min_profit_threshold = min_profit_threshold
        self.triangles = []
        
    def find_triangles(self, symbols: List[str]) -> List[List[str]]:
        """Find all possible triangular paths from available symbols"""
        base_currencies = set(symbol.split('/')[0] for symbol in symbols)
        triangles = []
        
        for base in base_currencies:
            # Find pairs that start with base currency
            first_pairs = [s for s in symbols if s.split('/')[0] == base]
            
            for first_pair in first_pairs:
                intermediate_currency = first_pair.split('/')[1]
                
                # Find pairs that start with intermediate currency
                second_pairs = [s for s in symbols if s.split('/')[0] == intermediate_currency]
                
                for second_pair in second_pairs:
                    final_currency = second_pair.split('/')[1]
                    
                    # Find pair that converts back to base currency
                    third_pair = f"{final_currency}/{base}"
                    if third_pair in symbols:
                        triangles.append([first_pair, second_pair, third_pair])
        
        self.triangles = triangles
        return triangles
    
    def calculate_arbitrage(self, prices: Dict[str, float], triangle: List[str]) -> Optional[ArbitrageOpportunity]:
        """Calculate arbitrage opportunity for a given triangle"""
        try:
            # Start with 1 unit of base currency
            initial_amount = 1.0
            
            # Execute triangular path
            pair1, pair2, pair3 = triangle
            
            # Step 1: Base -> Intermediate
            step1 = initial_amount * prices[pair1]
            
            # Step 2: Intermediate -> Final
            step2 = step1 * prices[pair2]
            
            # Step 3: Final -> Base
            final_amount = step2 * prices[pair3]
            
            profit_percentage = calculate_profit_percentage(initial_amount, final_amount)
            
            if profit_percentage >= self.min_profit_threshold:
                return ArbitrageOpportunity(
                    triangle=triangle,
                    profit_percentage=profit_percentage,
                    timestamp=np.datetime64('now'),
                    prices={pair: prices[pair] for pair in triangle}
                )
                
        except Exception as e:
            logger.error(f"Error calculating arbitrage for {triangle}: {e}")
            
        return None
    
    def scan_opportunities(self, prices: Dict[str, float]) -> List[ArbitrageOpportunity]:
        """Scan all triangles for arbitrage opportunities"""
        opportunities = []
        
        for triangle in self.triangles:
            opportunity = self.calculate_arbitrage(prices, triangle)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by profit percentage (highest first)
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        return opportunities