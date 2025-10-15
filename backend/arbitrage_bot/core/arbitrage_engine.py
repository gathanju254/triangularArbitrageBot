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

        if not valid_symbols:
            logger.warning("No valid symbols found for triangle detection")
            return []

        # Build currency graph: base -> list of (quote, pair)
        graph = {}
        for symbol in valid_symbols:
            try:
                base, quote = symbol.split('/')
                graph.setdefault(base, []).append((quote, symbol))
                # ensure node exists for quote so traversal is safe
                graph.setdefault(quote, [])
            except ValueError:
                continue

        triangles = []
        visited = set()

        # Find all 3-currency cycles (currency1 -> currency2 -> currency3 -> currency1)
        for currency1 in graph:
            if currency1 not in self.supported_currencies:
                continue

            for currency2, pair1 in graph.get(currency1, []):
                if currency2 not in graph:
                    continue

                for currency3, pair2 in graph.get(currency2, []):
                    if currency3 == currency1:
                        continue

                    # third leg: currency3 -> currency1
                    for dest, pair3 in graph.get(currency3, []):
                        if dest == currency1:
                            triangle = [pair1, pair2, pair3]
                            # canonical key to avoid duplicates regardless of ordering
                            triangle_key = tuple(sorted(triangle))
                            if triangle_key not in visited:
                                triangles.append(triangle)
                                visited.add(triangle_key)

        self.triangles = triangles
        logger.info(f"Found {len(triangles)} triangular paths from {len(valid_symbols)} symbols")

        if triangles:
            logger.info(f"Triangle examples: {triangles[:3]}")

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

# Create a module-level engine instance so other modules can import it
arbitrage_engine = ArbitrageEngine()

# Export symbols
__all__ = ["ArbitrageEngine", "arbitrage_engine"]
