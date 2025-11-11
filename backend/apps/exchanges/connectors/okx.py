# backend/apps/exchanges/connectors/okx.py

import hmac
import hashlib
import time
import json
import requests
from typing import Dict, List, Optional, Any
from decimal import Decimal
from urllib.parse import urlencode
from django.utils import timezone

from .base import BaseExchangeConnector
from core.exceptions import ExchangeConnectionError, InvalidOrderError


class OkxConnector(BaseExchangeConnector):
    """OKX exchange connector implementation"""

    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None, demo: bool = False):
        super().__init__(api_key, api_secret)
        self.passphrase = passphrase
        
        if demo:
            self.base_url = 'https://www.okx.com'
        else:
            self.base_url = 'https://www.okx.com'
        
        self.rate_limit_delay = 0.1  # 10 requests per second
        self.recv_window = 5000  # 5 seconds

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get OKX authentication headers"""
        if not self.api_key:
            return {}
            
        return {
            'OK-ACCESS-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

    def _sign_request(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Sign request with API secret using OKX signature format"""
        message = timestamp + method.upper() + request_path + body
        return hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format"""
        return timezone.now().isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    def _make_authenticated_request(self, endpoint: str, method: str = 'GET', 
                                  params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to OKX API"""
        if not self.api_key or not self.api_secret or not self.passphrase:
            raise ExchangeConnectionError("API credentials required for authenticated requests")

        # Prepare request
        timestamp = self._get_timestamp()
        request_path = endpoint
        
        # Handle query parameters
        if params and method.upper() == 'GET':
            request_path += '?' + urlencode(params)
        
        # Prepare body
        body = ""
        if data and method.upper() in ['POST', 'PUT']:
            body = json.dumps(data)

        # Generate signature
        signature = self._sign_request(timestamp, method, request_path, body)
        # Prepare headers
        headers = self._get_auth_headers()
        headers.update({
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
        })

        self._rate_limit()
        
        url = f"{self.base_url}{request_path if method.upper() == 'GET' else endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            result = response.json()
            
            # Check OKX response code
            if result.get('code') != '0':
                error_msg = result.get('msg', 'Unknown error')
                raise ExchangeConnectionError(f"OKX API error: {error_msg}")
                
            return result.get('data', [])
            
        except requests.exceptions.RequestException as e:
            raise ExchangeConnectionError(f"API request failed: {str(e)}")
        except ValueError as e:
            raise ExchangeConnectionError(f"Invalid JSON response: {str(e)}")

    def get_exchange_status(self) -> Dict[str, Any]:
        """Get OKX exchange status"""
        endpoint = '/api/v5/system/status'
        
        try:
            response = self._make_request(endpoint)
            
            status_data = response[0] if response else {}
            
            return {
                'is_online': True,
                'last_checked': timezone.now(),
                'response_time_ms': 0,  # Would need to measure actual response time
                'maintenance_mode': status_data.get('state') == 'maintain',
                'message': status_data.get('title', ''),
                'estimated_recovery_time': status_data.get('end')
            }
            
        except Exception as e:
            return {
                'is_online': False,
                'last_checked': timezone.now(),
                'response_time_ms': 0,
                'maintenance_mode': False,
                'message': str(e)
            }

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol"""
        endpoint = '/api/v5/market/ticker'
        params = {'instId': symbol}
        
        response = self._make_request(endpoint, params=params)
        
        if not response:
            raise ExchangeConnectionError(f"No ticker data found for {symbol}")
            
        ticker_data = response[0]
        
        bid_price = Decimal(ticker_data['bidPx']) if ticker_data['bidPx'] else Decimal('0')
        ask_price = Decimal(ticker_data['askPx']) if ticker_data['askPx'] else Decimal('0')
        last_price = Decimal(ticker_data['last']) if ticker_data['last'] else Decimal('0')
        
        spread = ((ask_price - bid_price) / bid_price * 100) if bid_price > 0 else Decimal('0')
        
        return {
            'symbol': symbol,
            'bid_price': bid_price,
            'ask_price': ask_price,
            'last_price': last_price,
            'volume_24h': Decimal(ticker_data.get('vol24h', '0')),
            'price_change_24h': Decimal(ticker_data.get('change24h', '0')),
            'price_change_percent_24h': Decimal(ticker_data.get('changePercent24h', '0')),
            'high_24h': Decimal(ticker_data.get('high24h', '0')),
            'low_24h': Decimal(ticker_data.get('low24h', '0')),
            'spread': spread,
            'timestamp': timezone.now()
        }

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol"""
        endpoint = '/api/v5/market/books'
        
        # OKX supports specific limit values
        okx_limits = {1: 1, 5: 5, 10: 10, 20: 20, 50: 50, 100: 100, 200: 200, 400: 400}
        okx_limit = okx_limits.get(limit, 100)
        
        params = {
            'instId': symbol,
            'sz': okx_limit
        }
        
        response = self._make_request(endpoint, params=params)
        
        if not response:
            raise ExchangeConnectionError(f"No order book data found for {symbol}")
            
        book_data = response[0]
        
        return {
            'symbol': symbol,
            'bids': [[Decimal(bid[0]), Decimal(bid[1])] for bid in book_data['bids'][:limit]],
            'asks': [[Decimal(ask[0]), Decimal(ask[1])] for ask in book_data['asks'][:limit]],
            'timestamp': timezone.now()
        }

    def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        endpoint = '/api/v5/account/balance'
        
        response = self._make_authenticated_request(endpoint)
        
        if not response:
            raise ExchangeConnectionError("No balance data received")
            
        balance_data = response[0]
        balances = {}
        
        for detail in balance_data.get('details', []):
            currency = detail['ccy']
            total = Decimal(detail['cashBal']) + Decimal(detail.get('availEq', '0'))
            
            if total > 0:
                balances[currency] = total
        
        return balances

    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order"""
        endpoint = '/api/v5/trade/order'
        
        # Map order types to OKX format
        order_type_map = {
            'market': 'market',
            'limit': 'limit',
            'stop': 'conditional'
        }
        
        okx_order_type = order_type_map.get(order_type.lower(), 'limit')
        
        order_data = {
            'instId': symbol,
            'tdMode': 'cash',  # cash, isolated, cross
            'side': 'buy' if side.lower() == 'buy' else 'sell',
            'ordType': okx_order_type,
            'sz': str(amount)
        }
        
        if price and okx_order_type == 'limit':
            order_data['px'] = str(price)
            
        if client_order_id:
            order_data['clOrdId'] = client_order_id
            
        # Set time in force
        if okx_order_type == 'limit':
            order_data['tgtCcy'] = 'base_ccy'  # or 'quote_ccy'
        
        response = self._make_authenticated_request(endpoint, method='POST', data=order_data)
        
        if not response:
            raise InvalidOrderError("No response received for order placement")
            
        order_result = response[0]
        
        return {
            'id': order_result['ordId'],
            'client_order_id': order_result.get('clOrdId'),
            'symbol': symbol,
            'side': side,
            'order_type': order_type,
            'amount': amount,
            'price': Decimal(order_result.get('px', '0')) if order_result.get('px') else None,
            'status': self._map_order_status(order_result.get('state')),
            'filled_amount': Decimal(order_result.get('fillSz', '0')),
            'average_price': Decimal(order_result.get('avgPx', '0')) if order_result.get('avgPx') else None,
            'fee': Decimal('0.00'),  # Would need separate endpoint for fees
            'raw_response': order_result
        }

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        endpoint = '/api/v5/trade/cancel-order'
        
        cancel_data = {
            'instId': symbol,
            'ordId': order_id
        }
        
        try:
            response = self._make_authenticated_request(endpoint, method='POST', data=cancel_data)
            return response and response[0].get('sCode') == '0'
        except ExchangeConnectionError:
            return False

    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status"""
        endpoint = '/api/v5/trade/order'
        params = {
            'instId': symbol,
            'ordId': order_id
        }
        
        response = self._make_authenticated_request(endpoint, params=params)
        
        if not response:
            raise ExchangeConnectionError(f"Order {order_id} not found")
            
        order_data = response[0]
        
        return {
            'id': order_data['ordId'],
            'symbol': symbol,
            'side': order_data['side'].lower(),
            'order_type': self._map_okx_order_type(order_data['ordType']),
            'amount': Decimal(order_data['sz']),
            'price': Decimal(order_data.get('px', '0')) if order_data.get('px') else None,
            'status': self._map_order_status(order_data.get('state')),
            'filled_amount': Decimal(order_data.get('fillSz', '0')),
            'average_price': Decimal(order_data.get('avgPx', '0')) if order_data.get('avgPx') else None,
            'fee': Decimal('0.00'),  # Would need separate endpoint for fees
            'created_time': order_data.get('cTime'),
            'updated_time': order_data.get('uTime'),
            'raw_response': order_data
        }

    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs"""
        endpoint = '/api/v5/public/instruments'
        params = {'instType': 'SPOT'}
        
        response = self._make_request(endpoint, params=params)
        
        pairs = []
        for instrument in response:
            if instrument['state'] == 'live':  # Only active instruments
                pair = {
                    'symbol': instrument['instId'],
                    'base_asset': instrument['baseCcy'],
                    'quote_asset': instrument['quoteCcy'],
                    'min_order_size': Decimal(instrument.get('minSz', '0')),
                    'max_order_size': Decimal(instrument.get('maxSz', '0')),
                    'price_precision': int(instrument.get('tickSz', '0.00000001').split('.')[1].count('0') + 1),
                    'amount_precision': int(instrument.get('lotSz', '0.00000001').split('.')[1].count('0') + 1),
                    'is_active': True
                }
                pairs.append(pair)
        
        return pairs

    def calculate_fees(self, symbol: str, amount: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Any]:
        """Calculate OKX fees"""
        # OKX has different fee tiers based on 30-day trading volume
        # Using standard maker/taker fees for simplicity
        trade_volume = amount * price
        
        # Standard fees (would need to get actual fee tier from account)
        maker_fee = Decimal('0.0008')  # 0.08%
        taker_fee = Decimal('0.0010')  # 0.10%
        
        # Use maker fee for limit orders, taker for market orders
        fee_percentage = maker_fee  # Default to maker fee
        
        fee_amount = trade_volume * fee_percentage
        
        return {
            'fee_percentage': float(fee_percentage),
            'fee_amount': float(fee_amount),
            'fee_currency': symbol.split('-')[1] if '-' in symbol else 'USDT',
            'total_cost': float(trade_volume + fee_amount) if side == 'buy' else float(trade_volume - fee_amount),
            'fee_tier': 'standard'
        }

    def _map_order_status(self, okx_status: str) -> str:
        """Map OKX order status to standard status"""
        status_map = {
            'canceled': 'cancelled',
            'live': 'open',
            'partially_filled': 'partial',
            'filled': 'filled',
            'mmp_canceled': 'cancelled'
        }
        return status_map.get(okx_status, okx_status)

    def _map_okx_order_type(self, okx_order_type: str) -> str:
        """Map OKX order type to standard order type"""
        type_map = {
            'market': 'market',
            'limit': 'limit',
            'conditional': 'stop'
        }
        return type_map.get(okx_order_type, okx_order_type)

    def validate_credentials(self) -> bool:
        """Validate API credentials by testing balance endpoint"""
        try:
            self.get_balance()
            return True
        except Exception:
            return False

    def get_server_time(self) -> Dict[str, Any]:
        """Get OKX server time"""
        endpoint = '/api/v5/public/time'
        
        response = self._make_request(endpoint)
        
        if response:
            return {
                'server_time': response[0]['ts'],
                'is_fallback': False
            }
        else:
            # Fallback to local time
            return {
                'server_time': int(time.time() * 1000),
                'is_fallback': True
            }

    def get_funding_balance(self) -> Dict[str, Decimal]:
        """Get funding account balance (separate from trading balance)"""
        endpoint = '/api/v5/asset/balances'
        
        response = self._make_authenticated_request(endpoint)
        
        balances = {}
        for balance in response:
            currency = balance['ccy']
            total = Decimal(balance['bal'])
            
            if total > 0:
                balances[currency] = total
        
        return balances

    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history"""
        endpoint = '/api/v5/trade/orders-history'
        params = {
            'instType': 'SPOT',
            'limit': limit
        }
        
        if symbol:
            params['instId'] = symbol
            
        response = self._make_authenticated_request(endpoint, params=params)
        
        orders = []
        for order_data in response:
            order = {
                'id': order_data['ordId'],
                'symbol': order_data['instId'],
                'side': order_data['side'].lower(),
                'order_type': self._map_okx_order_type(order_data['ordType']),
                'amount': Decimal(order_data['sz']),
                'price': Decimal(order_data.get('px', '0')) if order_data.get('px') else None,
                'status': self._map_order_status(order_data.get('state')),
                'filled_amount': Decimal(order_data.get('fillSz', '0')),
                'average_price': Decimal(order_data.get('avgPx', '0')) if order_data.get('avgPx') else None,
                'created_time': order_data.get('cTime'),
                'updated_time': order_data.get('uTime')
            }
            orders.append(order)
        
        return orders