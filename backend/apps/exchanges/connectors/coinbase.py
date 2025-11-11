# backend/apps/exchanges/connectors/coinbase.py

import hmac
import hashlib
import base64
import time
import json
from typing import Any, Dict, List, Optional
from decimal import Decimal
from django.utils import timezone

from .base import BaseExchangeConnector
from core.exceptions import ExchangeConnectionError, InvalidOrderError


class CoinbaseConnector(BaseExchangeConnector):
    """Coinbase Pro exchange connector"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None, sandbox: bool = False):
        super().__init__(api_key, api_secret)
        self.passphrase = passphrase
        
        if sandbox:
            self.base_url = 'https://api-public.sandbox.exchange.coinbase.com'
        else:
            self.base_url = 'https://api.exchange.coinbase.com'
        
        self.rate_limit_delay = 0.3  # 3 requests per second
    
    def _get_auth_headers(self, method: str, request_path: str, body: str = '') -> Dict[str, str]:
        """Get Coinbase authentication headers"""
        if not self.api_key or not self.api_secret or not self.passphrase:
            return {}
            
        timestamp = str(time.time())
        message = timestamp + method.upper() + request_path + body
        
        # Coinbase requires base64 decoding of the secret
        secret_b64 = base64.b64decode(self.api_secret)
        signature = hmac.new(
            secret_b64,
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()
        
        return {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
    
    def _make_authenticated_request(self, endpoint: str, method: str = 'GET', 
                                  params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to Coinbase API"""
        if not self.api_key or not self.api_secret or not self.passphrase:
            raise ExchangeConnectionError("API credentials required for authenticated requests")

        # Prepare request body
        body = ''
        if data and method.upper() in ['POST', 'PUT']:
            body = json.dumps(data)

        # Get authenticated headers
        headers = self._get_auth_headers(method, endpoint, body)
        
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
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
            
            # Coinbase returns empty body for some successful requests
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ExchangeConnectionError(f"API request failed: {str(e)}")
        except ValueError as e:
            raise ExchangeConnectionError(f"Invalid JSON response: {str(e)}")
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """Get Coinbase exchange status"""
        try:
            # Use time endpoint to check status
            response = self._make_request('/time')
            
            return {
                'status': 'online',
                'message': 'Coinbase exchange is operational',
                'timestamp': int(time.time() * 1000),
                'is_online': True,
                'server_time': response.get('iso'),
                'epoch': response.get('epoch')
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': int(time.time() * 1000),
                'is_online': False
            }
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol"""
        # Coinbase uses format like BTC-USD, ETH-USD
        coinbase_symbol = symbol.replace('/', '-')
        
        response = self._make_request(f'/products/{coinbase_symbol}/ticker')
        
        return {
            'symbol': symbol,
            'bid': Decimal(response.get('bid', 0)),
            'ask': Decimal(response.get('ask', 0)),
            'last': Decimal(response.get('price', 0)),
            'volume_24h': Decimal(response.get('volume', 0)),
            'volume_30d': Decimal(response.get('volume_30day', 0)),
            'high_24h': Decimal(0),  # Not provided in ticker endpoint
            'low_24h': Decimal(0),   # Not provided in ticker endpoint
            'open_24h': Decimal(0),  # Not provided in ticker endpoint
            'spread': (Decimal(response.get('ask', 0)) - Decimal(response.get('bid', 0))) / Decimal(response.get('bid', 1)) * 100,
            'timestamp': timezone.now()
        }
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol"""
        coinbase_symbol = symbol.replace('/', '-')
        
        # Coinbase supports levels 1, 2, 3
        level = 2 if limit <= 100 else 3
        
        response = self._make_request(f'/products/{coinbase_symbol}/book', params={'level': level})
        
        return {
            'symbol': symbol,
            'bids': [[Decimal(bid[0]), Decimal(bid[1]), int(bid[2])] for bid in response.get('bids', [])],
            'asks': [[Decimal(ask[0]), Decimal(ask[1]), int(ask[2])] for ask in response.get('asks', [])],
            'sequence': response.get('sequence'),
            'timestamp': timezone.now()
        }
    
    def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        response = self._make_authenticated_request('/accounts')
        
        balances = {}
        for account in response:
            currency = account.get('currency')
            balance = Decimal(account.get('balance', 0))
            available = Decimal(account.get('available', 0))
            hold = Decimal(account.get('hold', 0))
            
            if balance > 0:
                balances[currency] = {
                    'total': balance,
                    'available': available,
                    'locked': hold
                }
        
        return balances
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order"""
        coinbase_symbol = symbol.replace('/', '-')
        
        order_data = {
            'product_id': coinbase_symbol,
            'side': side.lower(),
            'type': order_type.lower(),
            'size': str(amount)
        }
        
        if order_type.lower() == 'limit':
            if not price:
                raise InvalidOrderError("Price required for limit orders")
            order_data['price'] = str(price)
            order_data['post_only'] = True  # Default to post-only for limit orders
        
        if client_order_id:
            order_data['client_oid'] = client_order_id
            
        # Set time in force
        if order_type.lower() == 'limit':
            order_data['time_in_force'] = 'GTC'  # Good Till Cancelled
        
        response = self._make_authenticated_request('/orders', method='POST', data=order_data)
        
        return {
            'id': response.get('id'),
            'client_order_id': response.get('client_oid'),
            'symbol': symbol,
            'side': side,
            'order_type': order_type,
            'amount': amount,
            'price': Decimal(response.get('price', 0)) if response.get('price') else None,
            'status': response.get('status', 'pending'),
            'filled_amount': Decimal(response.get('filled_size', 0)),
            'executed_value': Decimal(response.get('executed_value', 0)),
            'fill_fees': Decimal(response.get('fill_fees', 0)),
            'created_at': response.get('created_at'),
            'timestamp': timezone.now()
        }
    
    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order"""
        try:
            response = self._make_authenticated_request(f'/orders/{order_id}', method='DELETE')
            return True
        except ExchangeConnectionError:
            return False
    
    def get_order(self, order_id: str, symbol: str = None) -> Dict[str, Any]:
        """Get order status"""
        response = self._make_authenticated_request(f'/orders/{order_id}')
        
        return {
            'id': response.get('id'),
            'client_order_id': response.get('client_oid'),
            'symbol': response.get('product_id').replace('-', '/'),
            'side': response.get('side'),
            'order_type': response.get('type'),
            'amount': Decimal(response.get('size', 0)),
            'price': Decimal(response.get('price', 0)) if response.get('price') else None,
            'status': response.get('status'),
            'filled_amount': Decimal(response.get('filled_size', 0)),
            'executed_value': Decimal(response.get('executed_value', 0)),
            'fill_fees': Decimal(response.get('fill_fees', 0)),
            'average_price': Decimal(response.get('executed_value', 0)) / Decimal(response.get('filled_size', 1)) if Decimal(response.get('filled_size', 0)) > 0 else None,
            'created_at': response.get('created_at'),
            'done_at': response.get('done_at'),
            'done_reason': response.get('done_reason'),
            'timestamp': timezone.now()
        }
    
    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs"""
        response = self._make_request('/products')
        
        pairs = []
        for product in response:
            if product.get('status') == 'online':
                pairs.append({
                    'symbol': product.get('id').replace('-', '/'),
                    'base_asset': product.get('base_currency'),
                    'quote_asset': product.get('quote_currency'),
                    'min_order_size': Decimal(product.get('base_min_size', 0)),
                    'max_order_size': Decimal(product.get('base_max_size', 0)),
                    'min_order_value': Decimal(product.get('min_market_funds', 0)),
                    'max_order_value': Decimal(product.get('max_market_funds', 0)),
                    'price_precision': len(product.get('quote_increment', '0.01').split('.')[1]) if '.' in product.get('quote_increment', '0.01') else 0,
                    'amount_precision': len(product.get('base_increment', '0.01').split('.')[1]) if '.' in product.get('base_increment', '0.01') else 0,
                    'tick_size': Decimal(product.get('quote_increment', '0.01')),
                    'step_size': Decimal(product.get('base_increment', '0.01')),
                    'is_active': True,
                    'trading_disabled': product.get('trading_disabled', False),
                    'cancel_only': product.get('cancel_only', False),
                    'limit_only': product.get('limit_only', False),
                    'post_only': product.get('post_only', False)
                })
        
        return pairs
    
    def calculate_fees(self, symbol: str, amount: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Any]:
        """Calculate Coinbase fees"""
        # Coinbase has maker-taker fee structure
        trade_volume = amount * price
        
        # Standard fees (would need to get actual fee tier from account)
        maker_fee = Decimal('0.0040')  # 0.40%
        taker_fee = Decimal('0.0060')  # 0.60%
        
        # Use maker fee for limit orders, taker for market orders
        # For calculation purposes, we'll use taker fee as default
        fee_percentage = taker_fee
        
        fee_amount = trade_volume * fee_percentage
        
        return {
            'fee_percentage': float(fee_percentage),
            'fee_amount': float(fee_amount),
            'fee_currency': symbol.split('/')[1] if '/' in symbol else 'USD',
            'total_cost': float(trade_volume + fee_amount) if side == 'buy' else float(trade_volume - fee_amount),
            'fee_tier': 'standard',
            'exchange': 'coinbase'
        }
    
    def get_server_time(self) -> Dict[str, Any]:
        """Get Coinbase server time"""
        response = self._make_request('/time')
        return {
            'server_time': response.get('epoch'),
            'iso_time': response.get('iso'),
            'is_fallback': False
        }
    
    def get_product_stats(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr stats for a product"""
        coinbase_symbol = symbol.replace('/', '-')
        response = self._make_request(f'/products/{coinbase_symbol}/stats')
        
        return {
            'symbol': symbol,
            'open': Decimal(response.get('open', 0)),
            'high': Decimal(response.get('high', 0)),
            'low': Decimal(response.get('low', 0)),
            'last': Decimal(response.get('last', 0)),
            'volume': Decimal(response.get('volume', 0)),
            'volume_30day': Decimal(response.get('volume_30day', 0)),
            'timestamp': timezone.now()
        }
    
    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history"""
        params = {'limit': limit}
        if symbol:
            coinbase_symbol = symbol.replace('/', '-')
            params['product_id'] = coinbase_symbol
            
        response = self._make_authenticated_request('/orders', params=params)
        
        orders = []
        for order_data in response:
            order = {
                'id': order_data.get('id'),
                'symbol': order_data.get('product_id').replace('-', '/'),
                'side': order_data.get('side'),
                'order_type': order_data.get('type'),
                'amount': Decimal(order_data.get('size', 0)),
                'price': Decimal(order_data.get('price', 0)) if order_data.get('price') else None,
                'status': order_data.get('status'),
                'filled_amount': Decimal(order_data.get('filled_size', 0)),
                'executed_value': Decimal(order_data.get('executed_value', 0)),
                'fill_fees': Decimal(order_data.get('fill_fees', 0)),
                'created_at': order_data.get('created_at'),
                'done_at': order_data.get('done_at')
            }
            orders.append(order)
        
        return orders
    
    def validate_credentials(self) -> bool:
        """Validate API credentials"""
        try:
            self.get_balance()
            return True
        except Exception:
            return False