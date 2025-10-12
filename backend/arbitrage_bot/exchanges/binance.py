# backend/arbitrage_bot/exchanges/binance.py
import os
from typing import Dict, List
from .base_exchange import BaseExchange
import ccxt
import logging

logger = logging.getLogger(__name__)

class BinanceClient(BaseExchange):
    def __init__(self):
        api_key = os.getenv('BINANCE_API_KEY', '')
        secret_key = os.getenv('BINANCE_SECRET_KEY', '')
        super().__init__('binance', api_key, secret_key)
        
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': False,
            'enableRateLimit': True,
        })
    
    def get_ticker(self, symbol: str) -> Dict:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume']
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}
    
    def get_all_tickers(self) -> Dict[str, float]:
        try:
            tickers = self.exchange.fetch_tickers()
            return {symbol: data['last'] for symbol, data in tickers.items() if data['last'] is not None}
        except Exception as e:
            logger.error(f"Error fetching all tickers: {e}")
            return {}
    
    def get_symbols(self) -> List[str]:
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []
    
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None) -> Dict:
        try:
            if not self.is_authenticated:
                raise Exception("API credentials not configured")
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price
            )
            return order
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    def get_order(self, order_id: str, symbol: str) -> Dict:
        try:
            if not self.is_authenticated:
                raise Exception("API credentials not configured")
            
            return self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error fetching order: {e}")
            raise