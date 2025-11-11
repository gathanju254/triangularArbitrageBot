# backend/apps/exchanges/connectors/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
import time
import requests
from django.utils import timezone

from core.exceptions import ExchangeConnectionError, InvalidOrderError


class BaseExchangeConnector(ABC):
    """Abstract base class for exchange connectors"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = None
        self.rate_limit_delay = 0.1  # Default delay between requests
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     params: Dict = None, data: Dict = None, 
                     authenticated: bool = False) -> Dict[str, Any]:
        """
        Make HTTP request to exchange API with error handling.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body data
            authenticated: Whether to use authentication
            
        Returns:
            Dict: API response
            
        Raises:
            ExchangeConnectionError: If request fails
        """
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(authenticated)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ExchangeConnectionError(f"API request failed: {str(e)}")
        except ValueError as e:
            raise ExchangeConnectionError(f"Invalid JSON response: {str(e)}")
    
    def _get_headers(self, authenticated: bool = False) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            'User-Agent': 'Tudollar/1.0',
            'Content-Type': 'application/json'
        }
        
        if authenticated and self.api_key:
            headers.update(self._get_auth_headers())
        
        return headers
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_exchange_status(self) -> Dict[str, Any]:
        """Get exchange status"""
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol"""
        pass
    
    @abstractmethod
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol"""
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status"""
        pass
    
    @abstractmethod
    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs"""
        pass
    
    def validate_credentials(self) -> bool:
        """Validate API credentials"""
        try:
            # Try to fetch balance as a test
            self.get_balance()
            return True
        except Exception:
            return False
    
    def get_server_time(self) -> Dict[str, Any]:
        """Get server time (common method with fallback)"""
        try:
            return self._make_request('/api/v1/time')
        except ExchangeConnectionError:
            # Fallback to local time
            return {
                'serverTime': int(time.time() * 1000),
                'is_fallback': True
            }
    
    def calculate_fees(self, symbol: str, amount: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Any]:
        """Calculate estimated fees for a trade"""
        # Default implementation - should be overridden by specific exchanges
        trade_volume = amount * price
        fee_percentage = Decimal('0.001')  # Default 0.1%
        fee_amount = trade_volume * fee_percentage
        
        return {
            'fee_percentage': float(fee_percentage),
            'fee_amount': float(fee_amount),
            'total_cost': float(trade_volume + fee_amount) if side == 'buy' else float(trade_volume - fee_amount)
        }


class WebSocketConnector(ABC):
    """Abstract base class for WebSocket connections"""
    
    @abstractmethod
    def connect(self):
        """Connect to WebSocket"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from WebSocket"""
        pass
    
    @abstractmethod
    def subscribe_ticker(self, symbols: List[str]):
        """Subscribe to ticker updates"""
        pass
    
    @abstractmethod
    def subscribe_order_book(self, symbols: List[str]):
        """Subscribe to order book updates"""
        pass
    
    @abstractmethod
    def subscribe_trades(self, symbols: List[str]):
        """Subscribe to trade updates"""
        pass