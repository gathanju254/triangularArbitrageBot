# backend/arbitrage_bot/core/market_data.py
import asyncio
import websocket
import json
import logging
from typing import Dict, Callable
from ..exchanges.binance import BinanceClient
from ..exchanges.kraken import KrakenClient

logger = logging.getLogger(__name__)

class MarketDataManager:
    def __init__(self):
        self.exchanges = {
            'binance': BinanceClient(),
            'kraken': KrakenClient()
        }
        self.prices = {}
        self.subscribers = []
        
    def subscribe_prices(self, callback: Callable):
        """Subscribe to price updates"""
        self.subscribers.append(callback)
    
    def update_prices(self, exchange: str, new_prices: Dict[str, float]):
        """Update prices and notify subscribers"""
        self.prices.update(new_prices)
        
        # Notify all subscribers
        for callback in self.subscribers:
            try:
                callback(self.prices)
            except Exception as e:
                logger.error(f"Error in price subscriber: {e}")
    
    def start_websocket(self, exchange: str):
        """Start WebSocket connection for real-time data"""
        if exchange == 'binance':
            def on_message(ws, message):
                data = json.loads(message)
                if 's' in data and 'c' in data:
                    symbol = data['s'].replace('', '/')
                    price = float(data['c'])
                    self.update_prices(exchange, {symbol: price})
            
            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                logger.info("WebSocket connection closed")
                # Reconnect after 5 seconds
                asyncio.sleep(5)
                self.start_websocket(exchange)
            
            def on_open(ws):
                logger.info(f"WebSocket connected to {exchange}")
            
            # Connect to Binance WebSocket
            ws = websocket.WebSocketApp(
                "wss://stream.binance.com:9443/ws/!ticker@arr",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            ws.run_forever()