# backend/apps/exchanges/connectors/huobi.py

import hmac
import hashlib
import urllib.parse
import time
import requests
import base64
from typing import Dict, List, Any
from decimal import Decimal
from django.utils import timezone

from .base import BaseExchangeConnector
from core.exceptions import ExchangeConnectionError, InvalidOrderError


class HuobiConnector(BaseExchangeConnector):
    """Huobi exchange connector implementation"""

    def __init__(self, api_key: str = None, api_secret: str = None):
        super().__init__(api_key, api_secret)
        self.base_url = "https://api.huobi.pro"
        self.rate_limit_delay = 0.2  # Huobi rate limit
        self._access_key = api_key

    def _get_auth_headers(self) -> Dict[str, str]:
        """Implement Huobi authentication headers"""
        return {
            'User-Agent': 'Tudollar/1.0',
            'Content-Type': 'application/json'
        }

    def _sign_request(self, method: str, endpoint: str, params: Dict = None) -> Dict[str, str]:
        """Sign request for Huobi API authentication"""
        if not self.api_key or not self.api_secret:
            return {}
            
        timestamp = timezone.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        # Create signature payload
        sign_params = {
            'AccessKeyId': self.api_key,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp
        }
        
        if params:
            sign_params.update(params)
            
        # Sort parameters alphabetically
        sorted_params = '&'.join([f"{key}={urllib.parse.quote(str(value), safe='')}" 
                                for key, value in sorted(sign_params.items())])
        
        # Create signature string
        signature_string = f"{method.upper()}\napi.huobi.pro\n{endpoint}\n{sorted_params}"
        
        # Generate signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        signature_b64 = base64.b64encode(signature).decode()
        
        return {
            'Content-Type': 'application/json',
            'User-Agent': 'Tudollar/1.0',
            'AuthData': f'{self.api_key}:{signature_b64}'
        }

    def _make_authenticated_request(self, endpoint: str, method: str = 'GET', 
                                  params: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to Huobi API"""
        headers = self._sign_request(method, endpoint, params)
        
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        if params and method.upper() == 'GET':
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') != 'ok':
                error_msg = result.get('err-msg', 'Unknown error')
                raise ExchangeConnectionError(f"Huobi API error: {error_msg}")
                
            return result.get('data', {})
            
        except requests.exceptions.RequestException as e:
            raise ExchangeConnectionError(f"API request failed: {str(e)}")
        except ValueError as e:
            raise ExchangeConnectionError(f"Invalid JSON response: {str(e)}")

    def get_exchange_status(self) -> Dict[str, Any]:
        """Get Huobi exchange status"""
        try:
            # Huobi heartbeat endpoint
            response = self._make_request('/heartbeat/')
            
            return {
                'status': 'online',
                'message': 'Huobi exchange is operational',
                'timestamp': int(time.time() * 1000),
                'is_online': True
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': int(time.time() * 1000),
                'is_online': False
            }

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get Huobi ticker data"""
        huobi_symbol = symbol.replace('/', '').lower()
        
        response = self._make_request(f'/market/detail/merged', params={'symbol': huobi_symbol})
        
        ticker_data = response.get('tick', {})
        
        return {
            'symbol': symbol,
            'bid': float(ticker_data.get('bid', [0])[0]),
            'ask': float(ticker_data.get('ask', [0])[0]),
            'last': float(ticker_data.get('close', 0)),
            'open': float(ticker_data.get('open', 0)),
            'high_24h': float(ticker_data.get('high', 0)),
            'low_24h': float(ticker_data.get('low', 0)),
            'volume': float(ticker_data.get('vol', 0)),
            'amount': float(ticker_data.get('amount', 0)),
            'price_change': float(ticker_data.get('close', 0)) - float(ticker_data.get('open', 0)),
            'price_change_percent': ((float(ticker_data.get('close', 0)) - float(ticker_data.get('open', 0))) / 
                                   float(ticker_data.get('open', 1))) * 100,
            'timestamp': timezone.now()
        }

    def get_order_book(self, symbol: str, limit: int = 150) -> Dict[str, Any]:
        """Get Huobi order book"""
        huobi_symbol = symbol.replace('/', '').lower()
        
        # Huobi supports depth: 5, 10, 20, 150
        huobi_depth = 150 if limit > 20 else limit
        
        response = self._make_request(f'/market/depth', params={
            'symbol': huobi_symbol,
            'type': f'step{huobi_depth}'
        })
        
        book_data = response.get('tick', {})
        
        return {
            'symbol': symbol,
            'bids': [[float(bid[0]), float(bid[1])] for bid in book_data.get('bids', [])],
            'asks': [[float(ask[0]), float(ask[1])] for ask in book_data.get('asks', [])],
            'timestamp': book_data.get('ts', int(time.time() * 1000)),
            'version': book_data.get('version', 0)
        }

    def get_balance(self) -> Dict[str, Decimal]:
        """Get Huobi account balance"""
        endpoint = '/v1/account/accounts'
        response = self._make_authenticated_request(endpoint)
        
        balances = {}
        
        # Huobi returns multiple accounts (spot, margin, etc.)
        for account in response:
            if account.get('type') == 'spot':  # Use spot account
                account_id = account.get('id')
                
                # Get account balance
                balance_endpoint = f'/v1/account/accounts/{account_id}/balance'
                balance_response = self._make_authenticated_request(balance_endpoint)
                
                for balance_item in balance_response.get('list', []):
                    currency = balance_item.get('currency')
                    balance = Decimal(balance_item.get('balance', 0))
                    balance_type = balance_item.get('type')
                    
                    if balance > 0:
                        if currency not in balances:
                            balances[currency] = {
                                'total': Decimal(0),
                                'available': Decimal(0),
                                'locked': Decimal(0)
                            }
                        
                        if balance_type == 'trade':  # Available balance
                            balances[currency]['available'] += balance
                            balances[currency]['total'] += balance
                        elif balance_type == 'frozen':  # Locked balance
                            balances[currency]['locked'] += balance
                            balances[currency]['total'] += balance
        
        return balances

    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order on Huobi"""
        huobi_symbol = symbol.replace('/', '').lower()
        
        # Get account ID first
        accounts_response = self._make_authenticated_request('/v1/account/accounts')
        account_id = None
        for account in accounts_response:
            if account.get('type') == 'spot':
                account_id = account.get('id')
                break
        
        if not account_id:
            raise InvalidOrderError("No spot account found")
        
        order_data = {
            'account-id': account_id,
            'symbol': huobi_symbol,
            'type': f"{side.lower()}-{order_type.lower()}",
            'amount': str(amount),
            'source': 'api'
        }
        
        if price and order_type.lower() != 'market':
            order_data['price'] = str(price)
            
        if client_order_id:
            order_data['client-order-id'] = client_order_id
            
        response = self._make_authenticated_request('/v1/order/orders/place', 
                                                  method='POST', 
                                                  params=order_data)
        
        return {
            'order_id': response,
            'client_order_id': client_order_id,
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'status': 'submitted',
            'timestamp': timezone.now()
        }

    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order on Huobi"""
        try:
            response = self._make_authenticated_request(f'/v1/order/orders/{order_id}/submitcancel', 
                                                      method='POST')
            return response == order_id
        except Exception:
            return False

    def get_order(self, order_id: str, symbol: str = None) -> Dict[str, Any]:
        """Get order status from Huobi"""
        response = self._make_authenticated_request(f'/v1/order/orders/{order_id}')
        
        return {
            'order_id': response.get('id'),
            'client_order_id': response.get('client-order-id'),
            'symbol': response.get('symbol').upper(),
            'side': response.get('type', '').split('-')[0],
            'type': response.get('type', '').split('-')[1],
            'price': float(response.get('price', 0)),
            'amount': float(response.get('amount', 0)),
            'filled': float(response.get('filled-amount', 0)),
            'filled_cash': float(response.get('filled-cash-amount', 0)),
            'fee': float(response.get('field-fees', 0)),
            'status': response.get('state', ''),
            'created_at': response.get('created-at'),
            'finished_at': response.get('finished-at'),
            'timestamp': timezone.now()
        }

    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Huobi"""
        response = self._make_request('/v1/common/symbols')
        
        pairs = []
        for symbol_data in response:
            if symbol_data.get('state') == 'online':
                pairs.append({
                    'symbol': symbol_data.get('symbol').upper(),
                    'base_asset': symbol_data.get('base-currency').upper(),
                    'quote_asset': symbol_data.get('quote-currency').upper(),
                    'min_order_value': float(symbol_data.get('min-order-value', 0)),
                    'min_order_amount': float(symbol_data.get('min-order-amt', 0)),
                    'max_order_amount': float(symbol_data.get('max-order-amt', 0)),
                    'price_precision': symbol_data.get('price-precision', 8),
                    'amount_precision': symbol_data.get('amount-precision', 8),
                    'is_active': True
                })
        
        return pairs

    def calculate_fees(self, symbol: str, amount: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Any]:
        """Calculate Huobi fees"""
        # Huobi has different fee tiers based on HT holdings
        trade_volume = amount * price
        
        # Using standard taker fee (0.2%) for calculation
        fee_percentage = Decimal('0.002')  # 0.2%
        fee_amount = trade_volume * fee_percentage
        
        return {
            'fee_percentage': float(fee_percentage),
            'fee_amount': float(fee_amount),
            'fee_currency': symbol.split('/')[1] if '/' in symbol else 'USDT',
            'total_cost': float(trade_volume + fee_amount) if side == 'buy' else float(trade_volume - fee_amount),
            'exchange': 'huobi',
            'fee_tier': 'standard'
        }

    def get_server_time(self) -> Dict[str, Any]:
        """Get Huobi server time"""
        response = self._make_request('/v1/common/timestamp')
        return {
            'server_time': response,
            'is_fallback': False
        }

    def get_kline_data(self, symbol: str, period: str = '1min', size: int = 150) -> List[Dict[str, Any]]:
        """Get K-line/candlestick data"""
        huobi_symbol = symbol.replace('/', '').lower()
        
        response = self._make_request('/market/history/kline', params={
            'symbol': huobi_symbol,
            'period': period,
            'size': size
        })
        
        klines = []
        for kline in response:
            klines.append({
                'timestamp': kline.get('id'),
                'open': float(kline.get('open', 0)),
                'close': float(kline.get('close', 0)),
                'high': float(kline.get('high', 0)),
                'low': float(kline.get('low', 0)),
                'volume': float(kline.get('vol', 0)),
                'amount': float(kline.get('amount', 0))
            })
        
        return klines