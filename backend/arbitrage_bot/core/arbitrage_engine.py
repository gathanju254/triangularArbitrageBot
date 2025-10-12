# backend/arbitrage_bot/core/arbitrage_engine.py
# backend/arbitrage_bot/core/arbitrage_engine.py
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from ..models.arbitrage_opportunity import ArbitrageOpportunity
from ..utils.helpers import calculate_profit_percentage

logger = logging.getLogger(__name__)

class ArbitrageEngine:
    def __init__(self, min_profit_threshold: float = 0.2):
        self.min_profit_threshold = min_profit_threshold
        self.triangles = []
        self.supported_currencies = ['BTC', 'ETH', 'USDT', 'BNB', 'ADA', 'DOT', 'LINK', 'LTC', 'BCH', 'XRP']
        
    def find_triangles(self, symbols: List[str]) -> List[List[str]]:
        """Find all possible triangular paths from available symbols"""
        # Filter only major trading pairs with supported currencies
        valid_symbols = []
        for symbol in symbols:
            try:
                base, quote = symbol.split('/')
                if base in self.supported_currencies and quote in self.supported_currencies:
                    valid_symbols.append(symbol)
            except ValueError:
                logger.warning(f"Invalid symbol format: {symbol}")
                continue
        
        if not valid_symbols:
            logger.warning("No valid symbols found for triangle detection")
            return []
        
        # Get base currencies from valid symbols
        base_currencies = set()
        for symbol in valid_symbols:
            try:
                base, quote = symbol.split('/')
                base_currencies.add(base)
                base_currencies.add(quote)
            except ValueError:
                continue
        
        triangles = []
        
        for base in base_currencies:
            # Find pairs that start with base currency
            first_pairs = [s for s in valid_symbols if s.split('/')[0] == base]
            
            for first_pair in first_pairs:
                intermediate_currency = first_pair.split('/')[1]
                
                # Find pairs that start with intermediate currency
                second_pairs = [s for s in valid_symbols if s.split('/')[0] == intermediate_currency]
                
                for second_pair in second_pairs:
                    final_currency = second_pair.split('/')[1]
                    
                    # Find pair that converts back to base currency
                    third_pair = f"{final_currency}/{base}"
                    if third_pair in valid_symbols:
                        triangle = [first_pair, second_pair, third_pair]
                        # Avoid duplicate triangles
                        if triangle not in triangles:
                            triangles.append(triangle)
        
        self.triangles = triangles
        logger.info(f"Found {len(triangles)} triangular paths from {len(valid_symbols)} symbols")
        return triangles
    
    def calculate_arbitrage(self, prices: Dict[str, float], triangle: List[str]) -> Optional[ArbitrageOpportunity]:
        """Calculate arbitrage opportunity for a given triangle"""
        try:
            # Check if all required prices are available
            missing_pairs = [pair for pair in triangle if pair not in prices]
            if missing_pairs:
                logger.debug(f"Missing prices for pairs: {missing_pairs}")
                return None
            
            # Start with 1 unit of base currency
            initial_amount = 1.0
            current_amount = initial_amount
            
            # Track each step for debugging and display
            steps = []
            
            # Get the base currency from the first pair
            first_base, first_quote = triangle[0].split('/')
            
            # Execute triangular path with proper direction handling
            for i, pair in enumerate(triangle):
                base, quote = pair.split('/')
                
                if i == 0:
                    # First trade: Convert base to quote
                    # For A/B pair, price is how much B you get for 1 A
                    current_amount = current_amount * prices[pair]
                    steps.append(f"{initial_amount:.4f} {base} → {current_amount:.4f} {quote}")
                    
                elif i == 1:
                    # Second trade: Need to check currency alignment
                    prev_quote = triangle[i-1].split('/')[1]  # What we have from previous step
                    current_base, current_quote = pair.split('/')
                    
                    if prev_quote == current_base:
                        # Direct conversion: we have current_base, want current_quote
                        current_amount = current_amount * prices[pair]
                        steps.append(f"{(current_amount/prices[pair]):.4f} {current_base} → {current_amount:.4f} {current_quote}")
                    else:
                        # We have current_quote, want current_base (inverse trade)
                        current_amount = current_amount / prices[pair]
                        steps.append(f"{(current_amount*prices[pair]):.4f} {current_quote} → {current_amount:.4f} {current_base}")
                        
                elif i == 2:
                    # Final trade: Convert back to original base currency
                    current_base, current_quote = pair.split('/')
                    
                    if current_quote == first_base:
                        # Direct conversion to original base
                        current_amount = current_amount * prices[pair]
                        steps.append(f"{(current_amount/prices[pair]):.4f} {current_base} → {current_amount:.4f} {current_quote}")
                    else:
                        # Inverse conversion to original base
                        current_amount = current_amount / prices[pair]
                        steps.append(f"{(current_amount*prices[pair]):.4f} {current_quote} → {current_amount:.4f} {current_base}")
            
            final_amount = current_amount
            profit_percentage = calculate_profit_percentage(initial_amount, final_amount)
            
            if profit_percentage >= self.min_profit_threshold:
                logger.debug(f"Arbitrage opportunity found: {profit_percentage:.4f}% for {triangle}")
                logger.debug(f"Steps: {' → '.join(steps)}")
                
                return ArbitrageOpportunity(
                    triangle=triangle,
                    profit_percentage=profit_percentage,
                    timestamp=np.datetime64('now'),
                    prices={pair: prices[pair] for pair in triangle},
                    steps=steps
                )
            else:
                logger.debug(f"Arbitrage below threshold: {profit_percentage:.4f}% for {triangle}")
                
        except Exception as e:
            logger.error(f"Error calculating arbitrage for {triangle}: {e}")
            
        return None
    
    def scan_opportunities(self, prices: Dict[str, float]) -> List[ArbitrageOpportunity]:
        """Scan all triangles for arbitrage opportunities"""
        opportunities = []
        
        # Update triangles based on available prices if needed
        available_symbols = list(prices.keys())
        if not self.triangles and available_symbols:
            logger.info("Generating triangles from available symbols")
            self.find_triangles(available_symbols)
        
        if not self.triangles:
            logger.warning("No triangles available for scanning")
            return opportunities
        
        logger.debug(f"Scanning {len(self.triangles)} triangles for opportunities")
        
        for triangle in self.triangles:
            # Check if all required prices are available
            if all(pair in prices for pair in triangle):
                opportunity = self.calculate_arbitrage(prices, triangle)
                if opportunity:
                    opportunities.append(opportunity)
        
        # Sort by profit percentage (highest first)
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities "
                       f"(best: {opportunities[0].profit_percentage:.4f}%)")
        else:
            logger.debug("No arbitrage opportunities found above threshold")
        
        return opportunities
    
    def update_min_profit_threshold(self, new_threshold: float):
        """Update the minimum profit threshold"""
        old_threshold = self.min_profit_threshold
        self.min_profit_threshold = new_threshold
        logger.info(f"Updated profit threshold: {old_threshold}% -> {new_threshold}%")
    
    def get_triangle_statistics(self) -> Dict:
        """Get statistics about available triangles"""
        return {
            'total_triangles': len(self.triangles),
            'min_profit_threshold': self.min_profit_threshold,
            'supported_currencies': self.supported_currencies,
            'triangle_examples': self.triangles[:5] if self.triangles else []
        }
    
    def validate_triangle(self, triangle: List[str], prices: Dict[str, float]) -> Tuple[bool, str]:
        """Validate if a triangle can be executed with current prices"""
        try:
            # Check if all pairs exist
            missing_pairs = [pair for pair in triangle if pair not in prices]
            if missing_pairs:
                return False, f"Missing prices for: {missing_pairs}"
            
            # Check currency continuity
            for i in range(len(triangle)):
                current_pair = triangle[i]
                next_pair = triangle[(i + 1) % len(triangle)]
                
                current_base, current_quote = current_pair.split('/')
                next_base, next_quote = next_pair.split('/')
                
                # Check if currencies align properly
                # The quote currency of current pair should be the base currency of next pair
                # OR we should be able to do an inverse trade
                if current_quote != next_base and current_quote != next_quote:
                    return False, f"Currency mismatch between {current_pair} and {next_pair}"
            
            return True, "Triangle is valid"
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def get_available_triangles(self) -> List[List[str]]:
        """Get list of all available triangles"""
        return self.triangles.copy()
    
    def clear_triangles(self):
        """Clear cached triangles (force regeneration on next scan)"""
        old_count = len(self.triangles)
        self.triangles = []
        logger.info(f"Cleared {old_count} cached triangles")
    
    def find_triangles_with_currency(self, currency: str) -> List[List[str]]:
        """Find all triangles that involve a specific currency"""
        if not self.triangles:
            return []
        
        matching_triangles = []
        for triangle in self.triangles:
            # Check if the currency appears in any pair of the triangle
            for pair in triangle:
                if currency in pair:
                    matching_triangles.append(triangle)
                    break
        
        return matching_triangles

# Global arbitrage engine instance
arbitrage_engine = ArbitrageEngine()