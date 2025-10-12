# backend/arbitrage_bot/exchanges/base_exchange.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseExchange(ABC):
    def __init__(self, name: str, api_key: str = '', secret_key: str = ''):
        self.name = name
        self.api_key = api_key
        self.secret_key = secret_key
        self.is_authenticated = bool(api_key and secret_key)
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker price for symbol"""
        pass
    
    @abstractmethod
    def get_all_tickers(self) -> Dict[str, float]:
        """Get all available tickers"""
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[str]:
        """Get all available trading symbols"""
        pass
    
    @abstractmethod
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None) -> Dict:
        """Create a new order"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str, symbol: str) -> Dict:
        """Get order status"""
        pass
    
    def test_connection(self) -> bool:
        """Test exchange connection"""
        try:
            symbols = self.get_symbols()
            return len(symbols) > 0
        except Exception as e:
            logger.error(f"Connection test failed for {self.name}: {e}")
            return False