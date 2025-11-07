# backend/arbitrage_bot/core/arbitrage_engine.py
import logging
import numpy as np
import re
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

        logger.info(f"Available symbols for triangle detection: {len(valid_symbols)} symbols")
        
        if not valid_symbols:
            logger.warning("No valid symbols found for triangle detection")
            return []

        # Build complete currency graph with both directions
        graph = {}
        for symbol in valid_symbols:
            try:
                base, quote = symbol.split('/')
                
                # Add base -> quote
                if base not in graph:
                    graph[base] = []
                graph[base].append((quote, symbol))
                
                # Add quote -> base (inverse relationship)
                if quote not in graph:
                    graph[quote] = []
                # For inverse, we need to handle the rate conversion
                graph[quote].append((base, symbol))
                
            except ValueError:
                continue

        triangles = []
        visited = set()

        # Find 3-currency cycles using a depth-limited approach
        currencies = list(graph.keys())
        
        for currency_a in currencies:
            if currency_a not in self.supported_currencies:
                continue
                
            # First leg: A -> B
            for currency_b, pair_ab in graph.get(currency_a, []):
                if currency_b == currency_a:
                    continue
                    
                # Second leg: B -> C  
                for currency_c, pair_bc in graph.get(currency_b, []):
                    if currency_c == currency_a or currency_c == currency_b:
                        continue
                        
                    # Third leg: C -> A
                    for currency_d, pair_ca in graph.get(currency_c, []):
                        if currency_d == currency_a:
                            # We found a triangle: A->B->C->A
                            triangle = [pair_ab, pair_bc, pair_ca]
                            triangle_key = tuple(sorted(triangle))
                            
                            if triangle_key not in visited:
                                # Validate that this is a proper triangle with 3 unique currencies
                                try:
                                    unique_currencies = set()
                                    for pair in triangle:
                                        b, q = pair.split('/')
                                        unique_currencies.add(b)
                                        unique_currencies.add(q)
                                    
                                    if len(unique_currencies) == 3:
                                        triangles.append(triangle)
                                        visited.add(triangle_key)
                                        logger.debug(f"Found valid triangle: {triangle}")
                                except Exception as e:
                                    logger.debug(f"Invalid triangle {triangle}: {e}")

        self.triangles = triangles
        logger.info(f"Found {len(triangles)} triangular paths from {len(valid_symbols)} symbols")

        # Add manual fallback triangles if none found
        if not triangles:
            logger.warning("No triangles found automatically, adding manual triangles")
            manual_triangles = [
                ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'],
                ['ETH/USDT', 'ADA/ETH', 'ADA/USDT'],
                ['BTC/USDT', 'BNB/BTC', 'BNB/USDT'],
                ['ETH/USDT', 'DOT/ETH', 'DOT/USDT'],
                ['BTC/USDT', 'LINK/BTC', 'LINK/USDT'],
            ]
            
            # Filter to only include triangles where all pairs exist
            for triangle in manual_triangles:
                if all(pair in valid_symbols for pair in triangle):
                    triangles.append(triangle)
                    logger.info(f"✅ Added manual triangle: {triangle}")
            
            self.triangles = triangles

        if triangles:
            logger.info(f"Triangle examples: {triangles[:3]}")
        else:
            logger.error("❌ No triangles found at all!")

        return triangles
    
    def _sanitize_pair(self, pair: str) -> str:
        """Normalize and clean pair string (e.g. 'ETH/BTCv' -> 'ETH/BTC')."""
        if not isinstance(pair, str):
            return pair
        p = pair.strip().upper()
        # remove any character that is not alnum or '/'
        p = re.sub(r'[^A-Z0-9/]', '', p)

        # Normalize multiple slashes to single
        if p.count('/') > 1:
            parts = [part for part in p.split('/') if part]
            p = '/'.join(parts)

        # Ensure single slash and no accidental missing slash — best-effort split
        if '/' not in p and len(p) >= 6:
            for i in range(3, len(p) - 2):
                candidate = f"{p[:i]}/{p[i:]}"
                left, right = candidate.split('/')
                if left and right:
                    p = candidate
                    break

        return p

    def calculate_arbitrage(self, prices: Dict[str, float], triangle: List[str]) -> Optional[ArbitrageOpportunity]:
        """Calculate arbitrage opportunity for a given triangle.

        Tries all rotations and starting-currency choices. Sanitizes pairs before use.
        """
        try:
            # sanitize triangle pairs
            sanitized = [self._sanitize_pair(p) for p in triangle]
            # ensure prices keys are normalized (engine expects 'BASE/QUOTE' format)
            # Check availability
            missing_pairs = [pair for pair in sanitized if pair not in prices]
            if missing_pairs:
                logger.debug(f"Missing prices for pairs: {missing_pairs}")
                return None

            best_result = None

            # Try every rotation and both possible starting currencies for the first leg
            for rot in range(len(sanitized)):
                rotated = sanitized[rot:] + sanitized[:rot]
                # extract possible start currencies from first pair
                try:
                    a, b = rotated[0].split('/')
                except Exception:
                    continue
                start_options = [a, b]

                for start_currency in start_options:
                    initial_amount = 1.0
                    current_amount = initial_amount
                    current_currency = start_currency
                    steps = []
                    valid = True

                    for pair in rotated:
                        try:
                            base, quote = pair.split('/')
                        except ValueError:
                            valid = False
                            break

                        if current_currency == base:
                            # direct: base -> quote
                            rate = float(prices[pair])
                            prev_amount = current_amount
                            current_amount = current_amount * rate
                            steps.append(f"{prev_amount:.4f} {base} → {current_amount:.4f} {quote}")
                            current_currency = quote
                        elif current_currency == quote:
                            # inverse: quote -> base
                            rate = float(prices[pair])
                            prev_amount = current_amount
                            # guard division by zero
                            if rate == 0:
                                valid = False
                                break
                            current_amount = current_amount / rate
                            steps.append(f"{prev_amount:.4f} {quote} → {current_amount:.4f} {base}")
                            current_currency = base
                        else:
                            valid = False
                            break

                    if valid and current_currency == start_currency:
                        final_amount = current_amount
                        profit_percentage = calculate_profit_percentage(initial_amount, final_amount)
                        if profit_percentage >= self.min_profit_threshold:
                            # pick best opportunity by profit
                            if not best_result or profit_percentage > best_result['profit_percentage']:
                                best_result = {
                                    'triangle': rotated,
                                    'profit_percentage': profit_percentage,
                                    'final_amount': final_amount,
                                    'steps': steps,
                                    'prices': {pair: prices[pair] for pair in rotated}
                                }

            if best_result:
                logger.debug(f"Arbitrage opportunity found: {best_result['profit_percentage']:.4f}% for {best_result['triangle']}")
                logger.debug(f"Steps: {' → '.join(best_result['steps'])}")

                return ArbitrageOpportunity(
                    triangle=best_result['triangle'],
                    profit_percentage=best_result['profit_percentage'],
                    timestamp=np.datetime64('now'),
                    prices=best_result['prices'],
                    steps=best_result['steps']
                )

            logger.debug(f"No profitable arbitrage for triangle {triangle}")
            return None

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
        """Validate if a triangle can be executed with current prices.

        Tries rotations and starting currencies to determine if a valid cycle exists.
        """
        try:
            sanitized = [self._sanitize_pair(p) for p in triangle]

            # Quick check: all pairs must be strings with a slash
            for p in sanitized:
                if not isinstance(p, str) or '/' not in p:
                    return False, f"Invalid pair format: {p}"

            # Ensure pairs exist in prices (if prices provided)
            if prices:
                missing = [p for p in sanitized if p not in prices]
                if missing:
                    return False, f"Missing prices for: {missing}"

            # Try all rotations and start currencies
            for rot in range(len(sanitized)):
                rotated = sanitized[rot:] + sanitized[:rot]
                try:
                    first_base, first_quote = rotated[0].split('/')
                except Exception:
                    continue
                start_options = [first_base, first_quote]

                for start_currency in start_options:
                    current_currency = start_currency
                    valid = True

                    for pair in rotated:
                        try:
                            base, quote = pair.split('/')
                        except Exception:
                            valid = False
                            break

                        if current_currency == base:
                            current_currency = quote
                        elif current_currency == quote:
                            current_currency = base
                        else:
                            valid = False
                            break

                    if valid and current_currency == start_currency:
                        return True, "Triangle is valid"

            return False, "No valid execution ordering found for triangle"

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

    def add_manual_triangle(self, triangle: List[str]):
        """Manually add a triangle to the engine"""
        if triangle not in self.triangles:
            self.triangles.append(triangle)
            logger.info(f"Manually added triangle: {triangle}")
        else:
            logger.debug(f"Triangle already exists: {triangle}")

    def remove_triangle(self, triangle: List[str]):
        """Remove a specific triangle from the engine"""
        if triangle in self.triangles:
            self.triangles.remove(triangle)
            logger.info(f"Removed triangle: {triangle}")
        else:
            logger.warning(f"Triangle not found for removal: {triangle}")

# Create a module-level engine instance so other modules can import it
arbitrage_engine = ArbitrageEngine()

# Export symbols
__all__ = ["ArbitrageEngine", "arbitrage_engine"]