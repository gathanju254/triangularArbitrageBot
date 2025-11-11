# backend/apps/exchanges/connectors/kraken.py

import hmac
import hashlib
import base64
import time
import urllib.parse
from typing import Dict, List, Any
from decimal import Decimal
from django.utils import timezone
import requests

from .base import BaseExchangeConnector
from core.exceptions import ExchangeConnectionError, InvalidOrderError


class KrakenConnector(BaseExchangeConnector):
    """Kraken exchange connector implementation"""

    def __init__(self, api_key: str = None, api_secret: str = None):
        super().__init__(api_key, api_secret)
        self.base_url = "https://api.kraken.com"
        self.rate_limit_delay = 0.5  # Kraken rate limit
        self._api_version = '0'

    def _get_auth_headers(self) -> Dict[str, str]:
        """Implement Kraken authentication headers"""
        return {
            'User-Agent': 'Tudollar/1.0',
            'API-Key': self.api_key
        }

    def _sign_message(self, endpoint: str, data: Dict) -> str:
        """Sign message for Kraken API authentication"""
        if not self.api_secret:
            return ""
            
        postdata = urllib.parse.urlencode(data)
        encoded = (data['nonce'] + postdata).encode()
        message = endpoint.encode() + hashlib.sha256(encoded).digest()
        
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        )
        return base64.b64encode(signature.digest()).decode()

    def _make_authenticated_request(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to Kraken API"""
        if not self.api_key or not self.api_secret:
            raise ExchangeConnectionError("API credentials required for authenticated requests")

        data = data or {}
        data['nonce'] = str(int(time.time() * 1000))

        signature = self._sign_message(endpoint, data)

        headers = {
            'API-Key': self.api_key,
            'API-Sign': signature,
            'User-Agent': 'Tudollar/1.0'
        }

        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('error'):
                error_msg = ', '.join(result['error'])
                raise ExchangeConnectionError(f"Kraken API error: {error_msg}")
                
            return result.get('result', {})
            
        except requests.exceptions.RequestException as e:
            raise ExchangeConnectionError(f"API request failed: {str(e)}")
        except ValueError as e:
            raise ExchangeConnectionError(f"Invalid JSON response: {str(e)}")

    def get_exchange_status(self) -> Dict[str, Any]:
        """Get Kraken exchange status"""
        try:
            # Kraken doesn't have a direct status endpoint, so we'll use SystemStatus
            response = self._make_request('/0/public/SystemStatus')
            
            status = response.get('status', '')
            timestamp = response.get('timestamp', '')
            
            return {
                'status': 'online' if status == 'online' else 'offline',
                'message': response.get('message', ''),
                'timestamp': timestamp,
                'is_online': status == 'online'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': int(time.time() * 1000),
                'is_online': False
            }

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get Kraken ticker data"""
        # Convert symbol to Kraken format (e.g., BTC/USD -> XBTUSD)
        kraken_symbol = self._convert_symbol_to_kraken(symbol)
        
        response = self._make_request('/0/public/Ticker', params={'pair': kraken_symbol})
        
        # Kraken returns data with the symbol as key
        ticker_data = list(response.values())[0] if response else {}
        
        return {
            'symbol': symbol,
            'bid': float(ticker_data.get('b', [0])[0]),
            'ask': float(ticker_data.get('a', [0])[0]),
            'last': float(ticker_data.get('c', [0])[0]),
            'volume': float(ticker_data.get('v', [0])[0]),
            'volume_weighted_avg': float(ticker_data.get('p', [0])[0]),
            'high_24h': float(ticker_data.get('h', [0])[0]),
            'low_24h': float(ticker_data.get('l', [0])[0]),
            'price_change_24h': float(ticker_data.get('c', [0])[0]) - float(ticker_data.get('o', 0)),
            'number_of_trades': ticker_data.get('t', [0])[0],
            'timestamp': timezone.now()
        }

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get Kraken order book"""
        kraken_symbol = self._convert_symbol_to_kraken(symbol)
        
        response = self._make_request('/0/public/Depth', params={
            'pair': kraken_symbol,
            'count': limit
        })
        
        book_data = list(response.values())[0] if response else {}
        
        return {
            'symbol': symbol,
            'bids': [[float(bid[0]), float(bid[1]), float(bid[2])] for bid in book_data.get('bids', [])],
            'asks': [[float(ask[0]), float(ask[1]), float(ask[2])] for ask in book_data.get('asks', [])],
            'timestamp': timezone.now()
        }

    def get_balance(self) -> Dict[str, Decimal]:
        """Get Kraken account balance"""
        response = self._make_authenticated_request('/0/private/Balance')
        
        balances = {}
        for currency, balance_str in response.items():
            balance = Decimal(balance_str)
            if balance > 0:
                # Convert Kraken currency codes (XBT -> BTC, XETH -> ETH, etc.)
                normal_currency = self._convert_currency_from_kraken(currency)
                balances[normal_currency] = balance
        
        return balances

    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order on Kraken"""
        kraken_symbol = self._convert_symbol_to_kraken(symbol)
        
        order_data = {
            'pair': kraken_symbol,
            'type': side.lower(),
            'ordertype': order_type.lower(),
            'volume': str(amount),
            'oflags': 'post'  # Post-only order
        }
        
        if price and order_type.lower() != 'market':
            order_data['price'] = str(price)
            
        if client_order_id:
            order_data['userref'] = client_order_id
            
        response = self._make_authenticated_request('/0/private/AddOrder', order_data)
        
        txid = response.get('txid', [])
        
        return {
            'order_id': txid[0] if txid else None,
            'client_order_id': client_order_id,
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'status': 'open',
            'description': response.get('descr', {}).get('order', ''),
            'txids': txid,
            'timestamp': timezone.now()
        }

    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an order on Kraken"""
        try:
            response = self._make_authenticated_request('/0/private/CancelOrder', {
                'txid': order_id
            })
            return response.get('count', 0) > 0
        except Exception:
            return False

    def get_order(self, order_id: str, symbol: str = None) -> Dict[str, Any]:
        """Get order status from Kraken"""
        response = self._make_authenticated_request('/0/private/QueryOrders', {
            'txid': order_id,
            'trades': True  # Include trade info
        })
        
        order_data = response.get(order_id, {})
        
        return {
            'order_id': order_id,
            'symbol': self._convert_symbol_from_kraken(order_data.get('descr', {}).get('pair', '')),
            'side': order_data.get('descr', {}).get('type', ''),
            'type': order_data.get('descr', {}).get('ordertype', ''),
            'price': float(order_data.get('price', 0)),
            'amount': float(order_data.get('vol', 0)),
            'filled': float(order_data.get('vol_exec', 0)),
            'status': order_data.get('status', ''),
            'fee': float(order_data.get('fee', 0)),
            'open_time': float(order_data.get('opentm', 0)),
            'close_time': float(order_data.get('closetm', 0)) if order_data.get('closetm') else None,
            'timestamp': timezone.now()
        }

    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs from Kraken"""
        response = self._make_request('/0/public/AssetPairs')
        
        pairs = []
        for pair_id, pair_data in response.items():
            # Skip margin pairs and futures
            if pair_data.get('wsname'):
                pairs.append({
                    'symbol': pair_data['wsname'].replace('/', '-'),
                    'kraken_symbol': pair_id,
                    'base_asset': self._convert_currency_from_kraken(pair_data['base']),
                    'quote_asset': self._convert_currency_from_kraken(pair_data['quote']),
                    'altname': pair_data.get('altname', ''),
                    'min_order_volume': float(pair_data.get('ordermin', 0)),
                    'min_order_price': float(pair_data.get('costmin', 0)),
                    'price_precision': pair_data.get('pair_decimals', 8),
                    'amount_precision': pair_data.get('lot_decimals', 8),
                    'is_active': True
                })
        
        return pairs

    def calculate_fees(self, symbol: str, amount: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Any]:
        """Calculate Kraken fees"""
        # Kraken has volume-based fee tiers
        trade_volume = amount * price
        
        # Using standard maker fee (0.16%) for calculation
        # Actual fees depend on 30-day trading volume
        fee_percentage = Decimal('0.0016')  # 0.16%
        fee_amount = trade_volume * fee_percentage
        
        return {
            'fee_percentage': float(fee_percentage),
            'fee_amount': float(fee_amount),
            'fee_currency': symbol.split('/')[1] if '/' in symbol else 'USD',
            'total_cost': float(trade_volume + fee_amount) if side == 'buy' else float(trade_volume - fee_amount),
            'exchange': 'kraken',
            'fee_tier': 'standard'
        }

    def _convert_symbol_to_kraken(self, symbol: str) -> str:
        """Convert standard symbol format to Kraken format"""
        # Replace / with nothing and convert currencies
        base, quote = symbol.split('/')
        base_kraken = self._convert_currency_to_kraken(base)
        quote_kraken = self._convert_currency_to_kraken(quote)
        return f"{base_kraken}{quote_kraken}"

    def _convert_symbol_from_kraken(self, kraken_symbol: str) -> str:
        """Convert Kraken symbol format to standard format"""
        # This is simplified - would need proper mapping
        if kraken_symbol.startswith('XBT'):
            base = 'BTC'
            quote = kraken_symbol[3:]
        elif kraken_symbol.startswith('XETH'):
            base = 'ETH'
            quote = kraken_symbol[4:]
        else:
            base = kraken_symbol[:3]
            quote = kraken_symbol[3:]
            
        quote = self._convert_currency_from_kraken(quote)
        return f"{base}/{quote}"

    def _convert_currency_to_kraken(self, currency: str) -> str:
        """Convert standard currency to Kraken format"""
        kraken_map = {
            'BTC': 'XBT',
            'ETH': 'XETH',
            'USD': 'ZUSD',
            'EUR': 'ZEUR',
            'GBP': 'ZGBP',
            'CAD': 'ZCAD',
            'JPY': 'ZJPY'
        }
        return kraken_map.get(currency, currency)

    def _convert_currency_from_kraken(self, kraken_currency: str) -> str:
        """Convert Kraken currency to standard format"""
        standard_map = {
            'XBT': 'BTC',
            'XXBT': 'BTC',
            'XETH': 'ETH',
            'XXRP': 'XRP',
            'XLTC': 'LTC',
            'ZUSD': 'USD',
            'ZEUR': 'EUR',
            'ZGBP': 'GBP',
            'ZCAD': 'CAD',
            'ZJPY': 'JPY'
        }
        return standard_map.get(kraken_currency, kraken_currency)

    def get_server_time(self) -> Dict[str, Any]:
        """Get Kraken server time"""
        response = self._make_request('/0/public/Time')
        return {
            'server_time': response.get('unixtime', int(time.time())),
            'rfc1123': response.get('rfc1123', ''),
            'is_fallback': False
        }