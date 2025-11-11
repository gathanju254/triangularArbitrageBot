from .base import BaseExchangeConnector
import hmac
import hashlib
import base64
import time
from typing import Dict, List, Any
from decimal import Decimal
from urllib.parse import urlencode

class KucoinConnector(BaseExchangeConnector):
    """Kucoin exchange connector implementation"""

    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None):
        super().__init__(api_key, api_secret)
        self.base_url = "https://api.kucoin.com"
        self.passphrase = passphrase
        self.rate_limit_delay = 0.2  # Kucoin rate limit

    def _get_auth_headers(self) -> Dict[str, str]:
        """Implement Kucoin authentication headers"""
        if not self.api_key or not self.api_secret or not self.passphrase:
            return {}
        
        timestamp = str(int(time.time() * 1000))
        endpoint = "/api/v1/accounts"  # Default endpoint for signature
        
        # Create signature
        signature_string = timestamp + 'GET' + endpoint
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Passphrase signature
        passphrase_signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                self.passphrase.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        return {
            'KC-API-KEY': self.api_key,
            'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': timestamp,
            'KC-API-PASSPHRASE': passphrase_signature,
            'KC-API-KEY-VERSION': '2'
        }

    def get_exchange_status(self) -> Dict[str, Any]:
        """Get Kucoin exchange status"""
        try:
            response = self._make_request('/api/v1/status', 'GET')
            return {
                'status': 'online' if response.get('status') == 'open' else 'offline',
                'message': response.get('msg', ''),
                'timestamp': int(time.time() * 1000)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': int(time.time() * 1000)
            }

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get Kucoin ticker data"""
        response = self._make_request(f'/api/v1/market/orderbook/level1', 'GET', 
                                    params={'symbol': symbol})
        
        data = response.get('data', {})
        return {
            'symbol': symbol,
            'price': float(data.get('price', 0)),
            'bid': float(data.get('bestBid', 0)),
            'ask': float(data.get('bestAsk', 0)),
            'volume': float(data.get('size', 0)),
            'timestamp': int(time.time() * 1000)
        }

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get Kucoin order book"""
        response = self._make_request(f'/api/v1/market/orderbook/level2_{limit}', 'GET',
                                    params={'symbol': symbol})
        
        data = response.get('data', {})
        return {
            'symbol': symbol,
            'bids': [[float(price), float(amount)] for price, amount in data.get('bids', [])],
            'asks': [[float(price), float(amount)] for price, amount in data.get('asks', [])],
            'timestamp': data.get('time', int(time.time() * 1000))
        }

    def get_balance(self) -> Dict[str, Decimal]:
        """Get Kucoin account balance"""
        response = self._make_request('/api/v1/accounts', 'GET', authenticated=True)
        
        balances = {}
        for account in response.get('data', []):
            currency = account.get('currency')
            balance = Decimal(str(account.get('balance', 0)))
            available = Decimal(str(account.get('available', 0)))
            
            if balance > 0 or available > 0:
                balances[currency] = {
                    'total': balance,
                    'available': available,
                    'locked': balance - available
                }
        
        return balances

    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order on Kucoin"""
        
        order_data = {
            'clientOid': client_order_id or str(int(time.time() * 1000)),
            'side': side.lower(),
            'symbol': symbol,
            'type': order_type.lower(),
            'size': str(amount)
        }
        
        if price and order_type.lower() != 'market':
            order_data['price'] = str(price)
        
        response = self._make_request('/api/v1/orders', 'POST', 
                                    data=order_data, authenticated=True)
        
        data = response.get('data', {})
        return {
            'order_id': data.get('orderId'),
            'client_order_id': data.get('clientOid'),
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'status': 'open',
            'timestamp': int(time.time() * 1000)
        }

    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order on Kucoin"""
        try:
            response = self._make_request(f'/api/v1/orders/{order_id}', 'DELETE', 
                                        authenticated=True)
            return response.get('data', {}).get('cancelledOrderIds', []) != []
        except Exception:
            return False

    def get_order(self, order_id: str, symbol: str = None) -> Dict[str, Any]:
        """Get order status from Kucoin"""
        response = self._make_request(f'/api/v1/orders/{order_id}', 'GET',
                                    authenticated=True)
        
        data = response.get('data', {})
        return {
            'order_id': data.get('id'),
            'client_order_id': data.get('clientOid'),
            'symbol': data.get('symbol'),
            'side': data.get('side'),
            'type': data.get('type'),
            'price': float(data.get('price', 0)),
            'amount': float(data.get('size', 0)),
            'filled': float(data.get('filledSize', 0)),
            'status': data.get('status'),
            'timestamp': data.get('createdAt', int(time.time() * 1000))
        }

    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Kucoin"""
        response = self._make_request('/api/v1/symbols', 'GET')
        
        pairs = []
        for symbol_data in response.get('data', []):
            pairs.append({
                'symbol': symbol_data.get('symbol'),
                'base_asset': symbol_data.get('baseCurrency'),
                'quote_asset': symbol_data.get('quoteCurrency'),
                'min_price': float(symbol_data.get('priceIncrement', 0)),
                'min_quantity': float(symbol_data.get('baseMinSize', 0)),
                'max_quantity': float(symbol_data.get('baseMaxSize', 0)),
                'tick_size': float(symbol_data.get('priceIncrement', 0)),
                'step_size': float(symbol_data.get('baseIncrement', 0)),
                'status': symbol_data.get('enableTrading', False)
            })
        
        return pairs

    def calculate_fees(self, symbol: str, amount: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Any]:
        """Calculate Kucoin fees"""
        # Kucoin has tiered fees, but we'll use standard 0.1% for maker/taker
        trade_volume = amount * price
        fee_percentage = Decimal('0.001')  # 0.1%
        fee_amount = trade_volume * fee_percentage
        
        return {
            'fee_percentage': float(fee_percentage),
            'fee_amount': float(fee_amount),
            'fee_currency': symbol.split('-')[1] if '-' in symbol else 'USDT',
            'total_cost': float(trade_volume + fee_amount) if side == 'buy' else float(trade_volume - fee_amount),
            'exchange': 'kucoin'
        }

    def get_server_time(self) -> Dict[str, Any]:
        """Get Kucoin server time"""
        response = self._make_request('/api/v1/timestamp', 'GET')
        return {
            'serverTime': response.get('data'),
            'is_fallback': False
        }