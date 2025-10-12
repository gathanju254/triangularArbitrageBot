# backend/arbitrage_bot/core/market_data.py
import json
import logging
import threading
import time
from typing import Dict, Callable, List, Optional

# Use the standard websocket-client package
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logging.warning("websocket-client package not installed. Please run: pip install websocket-client")

logger = logging.getLogger(__name__)

class MarketDataManager:
    def __init__(self):
        self.exchanges = {
            'binance': None,  # We'll initialize these when needed
            'kraken': None
        }
        self.prices = {}
        self.subscribers: List[Callable] = []
        self.ws_connections = {}
        self.is_connected = False
        self._system_running = True
        self.last_update_time = {}
        self.reconnect_attempts = {}
        self.max_reconnect_attempts = 5
        
        # Supported trading pairs for WebSocket streams
        self.supported_pairs = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
            'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'XRPUSDT', 'EOSUSDT',
            'ETHBTC', 'ADABTC', 'DOTBTC', 'LINKBTC', 'LTCBTC'
        ]
        
    def subscribe_prices(self, callback: Callable):
        """Subscribe to price updates"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
            logger.info(f"New subscriber added. Total subscribers: {len(self.subscribers)}")
    
    def unsubscribe_prices(self, callback: Callable):
        """Unsubscribe from price updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Subscriber removed. Total subscribers: {len(self.subscribers)}")
    
    def update_prices(self, exchange: str, new_prices: Dict[str, float]):
        """Update prices and notify subscribers"""
        timestamp = time.time()
        
        # Update prices with timestamp
        for symbol, price in new_prices.items():
            self.prices[symbol] = {
                'price': price,
                'exchange': exchange,
                'timestamp': timestamp
            }
            self.last_update_time[symbol] = timestamp
        
        # Notify all subscribers with full price data
        for callback in self.subscribers:
            try:
                callback(self.prices)
            except Exception as e:
                logger.error(f"Error in price subscriber: {e}")
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if symbol in self.prices:
            price_data = self.prices[symbol]
            if isinstance(price_data, dict) and 'price' in price_data:
                return price_data['price']
            else:
                return price_data
        return None
    
    def get_all_prices(self) -> Dict:
        """Get all current prices"""
        return self.prices
    
    def start_websocket(self, exchange: str):
        """Start WebSocket connection for real-time data"""
        if not WEBSOCKET_AVAILABLE:
            logger.error("WebSocket client not available. Please install: pip install websocket-client")
            return
            
        if exchange in self.ws_connections:
            logger.info(f"WebSocket already running for {exchange}")
            return
        
        # Initialize reconnect attempts counter
        if exchange not in self.reconnect_attempts:
            self.reconnect_attempts[exchange] = 0
            
        if exchange == 'binance':
            self._start_binance_websocket()
        elif exchange == 'kraken':
            self._start_kraken_websocket()
        else:
            logger.error(f"Unsupported exchange for WebSocket: {exchange}")
    
    def _start_binance_websocket(self):
        """Start Binance WebSocket connection"""
        exchange = 'binance'
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                price_updates = {}
                
                # Handle different message types
                if 'stream' in data:
                    # Stream format with multiple symbols
                    stream_data = data['data']
                    if 's' in stream_data and 'c' in stream_data:
                        symbol = self._format_symbol(stream_data['s'])
                        price = float(stream_data['c'])
                        price_updates[symbol] = price
                elif 'e' in data and data['e'] == '24hrTicker':
                    # Individual ticker format
                    symbol = self._format_symbol(data['s'])
                    price = float(data['c'])
                    price_updates[symbol] = price
                elif isinstance(data, list):
                    # Array format for multiple tickers
                    for ticker in data:
                        if 's' in ticker and 'c' in ticker:
                            symbol = self._format_symbol(ticker['s'])
                            price = float(ticker['c'])
                            price_updates[symbol] = price
                
                if price_updates:
                    self.update_prices(exchange, price_updates)
                    logger.debug(f"Updated {len(price_updates)} prices from {exchange}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in WebSocket message: {e}")
            except KeyError as e:
                logger.error(f"Missing key in WebSocket data: {e}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket error for {exchange}: {error}")
            self.is_connected = False
        
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket connection closed for {exchange}")
            self.is_connected = False
            
            # Remove from active connections
            if exchange in self.ws_connections:
                del self.ws_connections[exchange]
            
            # Reconnect logic
            if self._system_running and self.reconnect_attempts[exchange] < self.max_reconnect_attempts:
                self.reconnect_attempts[exchange] += 1
                reconnect_delay = min(5 * self.reconnect_attempts[exchange], 30)  # Exponential backoff max 30s
                logger.info(f"Reconnecting to {exchange} in {reconnect_delay}s (attempt {self.reconnect_attempts[exchange]})")
                threading.Timer(reconnect_delay, lambda: self.start_websocket(exchange)).start()
            else:
                logger.error(f"Max reconnection attempts reached for {exchange}")
        
        def on_open(ws):
            logger.info(f"WebSocket connected to {exchange}")
            self.is_connected = True
            self.reconnect_attempts[exchange] = 0  # Reset reconnect attempts on successful connection
        
        try:
            # Create streams for individual symbols (more reliable than !ticker@arr)
            streams = [f"{symbol.lower()}@ticker" for symbol in self.supported_pairs]
            stream_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
            
            logger.info(f"Connecting to Binance WebSocket with {len(streams)} streams")
            
            ws = websocket.WebSocketApp(
                stream_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Store the connection
            self.ws_connections[exchange] = ws
            
            # Run in a separate thread
            def run_websocket():
                try:
                    ws.run_forever()
                except Exception as e:
                    logger.error(f"WebSocket run_forever error for {exchange}: {e}")
            
            thread = threading.Thread(target=run_websocket, name=f"WS-{exchange}")
            thread.daemon = True
            thread.start()
            
            logger.info(f"Started WebSocket thread for {exchange}")
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket for {exchange}: {e}")
            self.is_connected = False
    
    def _start_binance_individual_streams(self):
        """Alternative method using individual WebSocket connections for each symbol"""
        exchange = 'binance'
        
        def create_symbol_handler(symbol):
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if 'c' in data:
                        formatted_symbol = self._format_symbol(symbol)
                        price = float(data['c'])
                        self.update_prices(exchange, {formatted_symbol: price})
                except Exception as e:
                    logger.error(f"Error processing {symbol} WebSocket message: {e}")
            
            return on_message
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket connection closed")
        
        def on_open(ws):
            logger.info(f"WebSocket connected")
        
        # Start individual WebSocket for each symbol
        for symbol in self.supported_pairs[:5]:  # Limit to 5 for testing
            try:
                ws_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@ticker"
                ws = websocket.WebSocketApp(
                    ws_url,
                    on_message=create_symbol_handler(symbol),
                    on_error=on_error,
                    on_close=on_close,
                    on_open=on_open
                )
                
                thread = threading.Thread(target=ws.run_forever, name=f"WS-{symbol}")
                thread.daemon = True
                thread.start()
                
                self.ws_connections[f"{exchange}_{symbol}"] = ws
                
            except Exception as e:
                logger.error(f"Failed to start WebSocket for {symbol}: {e}")
    
    def _start_kraken_websocket(self):
        """Start Kraken WebSocket connection"""
        logger.info("Kraken WebSocket not yet implemented")
        # Kraken WebSocket implementation would go here
    
    def _format_symbol(self, symbol: str) -> str:
        """Format symbol from exchange format to internal format"""
        # Convert BTCUSDT to BTC/USDT
        if symbol.endswith('USDT'):
            return symbol.replace('USDT', '/USDT')
        elif symbol.endswith('BUSD'):
            return symbol.replace('BUSD', '/BUSD')
        elif symbol.endswith('ETH'):
            return symbol.replace('ETH', '/ETH')
        elif symbol.endswith('BTC'):
            return symbol.replace('BTC', '/BTC')
        else:
            # Try to split by common patterns
            for base in ['BTC', 'ETH', 'USDT', 'BNB', 'ADA', 'DOT', 'LINK', 'LTC', 'BCH', 'XRP']:
                if symbol.endswith(base):
                    quote = symbol[:-len(base)]
                    return f"{quote}/{base}"
            return symbol
    
    def start_all_websockets(self):
        """Start WebSocket connections for all supported exchanges"""
        if not WEBSOCKET_AVAILABLE:
            logger.error("WebSocket client not available. Please install: pip install websocket-client")
            return
            
        logger.info("Starting all WebSocket connections")
        self._system_running = True
        for exchange in self.exchanges.keys():
            self.start_websocket(exchange)
    
    def stop_websocket(self, exchange: str = None):
        """Stop WebSocket connections"""
        if exchange:
            # Stop specific exchange
            if exchange in self.ws_connections:
                try:
                    self.ws_connections[exchange].close()
                    logger.info(f"WebSocket connection closed for {exchange}")
                except Exception as e:
                    logger.error(f"Error closing WebSocket for {exchange}: {e}")
                finally:
                    if exchange in self.ws_connections:
                        del self.ws_connections[exchange]
        else:
            # Stop all exchanges
            self._system_running = False
            for exchange_name, ws in self.ws_connections.items():
                try:
                    ws.close()
                    logger.info(f"WebSocket connection closed for {exchange_name}")
                except Exception as e:
                    logger.error(f"Error closing WebSocket for {exchange_name}: {e}")
            
            self.ws_connections = {}
            self.is_connected = False
            logger.info("All WebSocket connections stopped")
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get connection status for all exchanges"""
        status = {}
        for exchange in self.exchanges.keys():
            status[exchange] = exchange in self.ws_connections
        return status
    
    def get_price_statistics(self) -> Dict:
        """Get statistics about current prices"""
        total_symbols = len(self.prices)
        current_time = time.time()
        recent_prices = {}
        
        for symbol, data in self.prices.items():
            if isinstance(data, dict) and 'timestamp' in data:
                if current_time - data['timestamp'] < 60:  # Prices from last 60 seconds
                    recent_prices[symbol] = data
            else:
                # If it's just a float price, consider it recent
                recent_prices[symbol] = data
        
        return {
            'total_symbols': total_symbols,
            'recent_symbols': len(recent_prices),
            'exchanges_connected': len([ex for ex in self.exchanges if ex in self.ws_connections]),
            'last_update': max(self.last_update_time.values()) if self.last_update_time else 0,
            'websocket_available': WEBSOCKET_AVAILABLE
        }
    
    def add_sample_prices(self):
        """Add sample prices for testing when WebSocket is not available"""
        sample_prices = {
            'BTC/USDT': 45000.0,
            'ETH/USDT': 2700.0,
            'ETH/BTC': 0.06,
            'ADA/USDT': 0.55,
            'ADA/BTC': 0.000012,
            'BNB/USDT': 320.0,
            'BNB/BTC': 0.0071,
            'DOT/USDT': 6.5,
            'DOT/BTC': 0.000144,
            'LINK/USDT': 14.2,
            'LINK/ETH': 0.0052
        }
        
        self.update_prices('sample', sample_prices)
        logger.info(f"Added {len(sample_prices)} sample prices for testing")

# Global market data manager instance
market_data_manager = MarketDataManager()

# Initialize with sample data if no WebSocket available
if not WEBSOCKET_AVAILABLE:
    logger.info("WebSocket not available, initializing with sample data")
    market_data_manager.add_sample_prices()