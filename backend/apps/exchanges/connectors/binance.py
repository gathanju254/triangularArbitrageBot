# backend/apps/exchanges/connectors/binance.py

import hmac
import hashlib
import time
from typing import Any, Dict, List, Optional
from decimal import Decimal
from urllib.parse import urlencode
from django.utils import timezone

from .base import BaseExchangeConnector
from core.exceptions import ExchangeConnectionError, InvalidOrderError


class BinanceConnector(BaseExchangeConnector):
    """Binance exchange connector"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        super().__init__(api_key, api_secret)
        
        if testnet:
            self.base_url = 'https://testnet.binance.vision/api/v3'
        else:
            self.base_url = 'https://api.binance.com/api/v3'
        
        self.rate_limit_delay = 0.1  # 10 requests per second
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Binance authentication headers"""
        return {
            'X-MBX-APIKEY': self.api_key
        }
    
    def _sign_request(self, params: Dict) -> str:
        """Sign request with API secret"""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """Get Binance exchange status"""
        endpoint = '/api/v3/ping'
        response = self._make_request(endpoint)
        
        # If we get here without exception, exchange is online
        return {
            'is_online': True,
            'last_checked': timezone.now(),
            'response_time_ms': 0,  # Would need to measure actual response time
            'maintenance_mode': False
        }
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol"""
        endpoint = '/api/v3/ticker/24hr'
        params = {'symbol': symbol.replace('/', '')}
        
        response = self._make_request(endpoint, params=params)
        
        return {
            'symbol': symbol,
            'bid_price': Decimal(response['bidPrice']),
            'ask_price': Decimal(response['askPrice']),
            'last_price': Decimal(response['lastPrice']),
            'volume_24h': Decimal(response['volume']),
            'price_change_24h': Decimal(response['priceChangePercent']),
            'spread': (Decimal(response['askPrice']) - Decimal(response['bidPrice'])) / Decimal(response['bidPrice']) * 100,
            'timestamp': timezone.now()
        }
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol"""
        endpoint = '/api/v3/depth'
        params = {
            'symbol': symbol.replace('/', ''),
            'limit': limit
        }
        
        response = self._make_request(endpoint, params=params)
        
        return {
            'symbol': symbol,
            'bids': [[Decimal(price), Decimal(quantity)] for price, quantity in response['bids']],
            'asks': [[Decimal(price), Decimal(quantity)] for price, quantity in response['asks']],
            'timestamp': timezone.now()
        }
    
    def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        if not self.api_key or not self.api_secret:
            raise ExchangeConnectionError("API credentials required for balance check")
        
        endpoint = '/api/v3/account'
        params = {
            'timestamp': int(time.time() * 1000),
            'recvWindow': 5000
        }
        
        params['signature'] = self._sign_request(params)
        response = self._make_request(endpoint, params=params, authenticated=True)
        
        balances = {}
        for balance in response['balances']:
            asset = balance['asset']
            free = Decimal(balance['free'])
            locked = Decimal(balance['locked'])
            total = free + locked
            
            if total > 0:
                balances[asset] = total
        
        return balances
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order"""
        if not self.api_key or not self.api_secret:
            raise ExchangeConnectionError("API credentials required for trading")
        
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol.replace('/', ''),
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': str(amount),
            'timestamp': int(time.time() * 1000),
            'recvWindow': 5000
        }
        
        if client_order_id:
            params['newClientOrderId'] = client_order_id
        
        if order_type.lower() == 'limit':
            if not price:
                raise InvalidOrderError("Price required for limit orders")
            params['price'] = str(price)
            params['timeInForce'] = 'GTC'
        
        params['signature'] = self._sign_request(params)
        
        response = self._make_request(
            endpoint, method='POST', params=params, authenticated=True
        )
        
        return {
            'id': response['orderId'],
            'client_order_id': response.get('clientOrderId'),
            'symbol': symbol,
            'side': side,
            'order_type': order_type,
            'amount': amount,
            'price': Decimal(response['price']) if 'price' in response else None,
            'status': response['status'].lower(),
            'filled_amount': Decimal(response['executedQty']),
            'fee': Decimal('0.00'),  # Would need to calculate based on trade
            'raw_response': response
        }
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        if not self.api_key or not self.api_secret:
            raise ExchangeConnectionError("API credentials required for order cancellation")
        
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol.replace('/', ''),
            'orderId': order_id,
            'timestamp': int(time.time() * 1000),
            'recvWindow': 5000
        }
        
        params['signature'] = self._sign_request(params)
        
        try:
            self._make_request(endpoint, method='DELETE', params=params, authenticated=True)
            return True
        except ExchangeConnectionError:
            return False
    
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status"""
        if not self.api_key or not self.api_secret:
            raise ExchangeConnectionError("API credentials required for order status")
        
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol.replace('/', ''),
            'orderId': order_id,
            'timestamp': int(time.time() * 1000),
            'recvWindow': 5000
        }
        
        params['signature'] = self._sign_request(params)
        response = self._make_request(endpoint, params=params, authenticated=True)
        
        return {
            'id': response['orderId'],
            'symbol': symbol,
            'side': response['side'].lower(),
            'order_type': response['type'].lower(),
            'amount': Decimal(response['origQty']),
            'price': Decimal(response['price']),
            'status': response['status'].lower(),
            'filled_amount': Decimal(response['executedQty']),
            'average_price': Decimal(response['cummulativeQuoteQty']) / Decimal(response['executedQty']) if Decimal(response['executedQty']) > 0 else None,
            'fee': Decimal('0.00'),  # Would need separate endpoint for fees
            'raw_response': response
        }
    
    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs"""
        endpoint = '/api/v3/exchangeInfo'
        response = self._make_request(endpoint)
        
        pairs = []
        for symbol_info in response['symbols']:
            if symbol_info['status'] == 'TRADING':
                pair = {
                    'symbol': symbol_info['symbol'],
                    'base_asset': symbol_info['baseAsset'],
                    'quote_asset': symbol_info['quoteAsset'],
                    'min_order_size': Decimal(symbol_info['filters'][1]['minQty']),
                    'max_order_size': Decimal(symbol_info['filters'][1]['maxQty']),
                    'price_precision': symbol_info['quotePrecision'],
                    'amount_precision': symbol_info['baseAssetPrecision'],
                    'is_active': True
                }
                pairs.append(pair)
        
        return pairs
    
    def calculate_fees(self, symbol: str, amount: Decimal, price: Decimal, 
                      side: str) -> Dict[str, Any]:
        """Calculate Binance fees"""
        # Binance has different fee tiers, using standard 0.1% for simplicity
        trade_volume = amount * price
        
        # Check if BNB discount available (simplified)
        has_bnb_discount = False  # This would require account info
        
        if has_bnb_discount:
            fee_percentage = Decimal('0.00075')  # 0.075% with BNB discount
        else:
            fee_percentage = Decimal('0.001')  # 0.1% standard
        
        fee_amount = trade_volume * fee_percentage
        
        return {
            'fee_percentage': float(fee_percentage),
            'fee_amount': float(fee_amount),
            'fee_currency': symbol.split('/')[1] if '/' in symbol else 'USDT',
            'total_cost': float(trade_volume + fee_amount) if side == 'buy' else float(trade_volume - fee_amount)
        }