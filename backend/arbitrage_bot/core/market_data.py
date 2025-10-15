# backend/arbitrage_bot/core/market_data.py
import json
import logging
import threading
import time
from typing import Dict, Callable, List, Optional
import importlib

logger = logging.getLogger(__name__)

# Use a robust import strategy for websocket-client
WEBSOCKET_AVAILABLE = False
websocket = None
WebSocketApp = None

try:
    # Try to import the public API first
    websocket = importlib.import_module('websocket')
    WebSocketApp = getattr(websocket, 'WebSocketApp', None)

    # If not exposed on package root, try the internal module where it's implemented
    if WebSocketApp is None:
        try:
            _app = importlib.import_module('websocket._app')
            WebSocketApp = getattr(_app, 'WebSocketApp', None)
        except Exception:
            WebSocketApp = None

    if WebSocketApp and websocket:
        # Ensure the attribute is accessible on the module object
        setattr(websocket, 'WebSocketApp', WebSocketApp)
        WEBSOCKET_AVAILABLE = True
    else:
        raise ImportError("WebSocketApp not found in 'websocket' package")

except Exception as e:
    WEBSOCKET_AVAILABLE = False
    websocket = None
    WebSocketApp = None
    logger.warning(
        "websocket-client not available or wrong 'websocket' package installed. "
        "Install websocket-client ([pip install websocket-client](http://_vscodecontentref_/2)) and ensure no local module named "
        "'websocket.py' shadows it. Details: %s", e
    )

class MarketDataManager:
    def __init__(self):
        self.exchanges = {
            'binance': None,
            'kraken': None
        }
        self.prices = {}
        self.subscribers: List[Callable] = []
        self.ws_connections = {}
        self.ws_lock = threading.Lock()
        self.is_connected = False
        self._system_running = True
        self.last_update_time = {}
        self.reconnect_attempts = {}
        self.max_reconnect_attempts = 5
        self._health_thread = None
        self._health_thread_stop = threading.Event()
        
        # Supported currencies for symbol formatting
        self.supported_currencies = ['BTC', 'ETH', 'USDT', 'ADA', 'BNB', 'DOT', 'LINK', 'LTC', 'BCH', 'XRP', 'EOS']
        
        # Accept both formatted symbols ("BTC/USDT") and exchange style ("BTCUSDT")
        self.supported_pairs = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT',
            'LINK/USDT', 'LTC/USDT', 'BCH/USDT', 'XRP/USDT', 'EOS/USDT',
            'ETH/BTC', 'ADA/BTC', 'DOT/BTC', 'LINK/BTC', 'LTC/BTC',
            'BNB/ETH', 'ADA/ETH', 'DOT/ETH', 'LINK/ETH'
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
            # Ensure we have the proper symbol format
            formatted_symbol = self._format_symbol(symbol)
            
            self.prices[formatted_symbol] = {
                'price': price,
                'exchange': exchange,
                'timestamp': timestamp
            }
            self.last_update_time[formatted_symbol] = timestamp
        
        # Log price updates for debugging
        if new_prices:
            sample_symbol = list(new_prices.keys())[0]
            logger.debug(f"Updated {len(new_prices)} prices from {exchange}. Sample: {sample_symbol} = {new_prices[sample_symbol]}")
        
        # Notify all subscribers with full price data
        for callback in self.subscribers:
            try:
                callback(self.prices)
            except Exception as e:
                logger.error(f"Error in price subscriber: {e}")
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        formatted_symbol = self._format_symbol(symbol)
        if formatted_symbol in self.prices:
            price_data = self.prices[formatted_symbol]
            if isinstance(price_data, dict) and 'price' in price_data:
                return price_data['price']
            else:
                return price_data
        return None
    
    def get_all_prices(self) -> Dict:
        """Get all current prices"""
        return self.prices
    
    def _format_symbol(self, symbol: str) -> str:
        """Format symbol to standard format (BASE/QUOTE)"""
        if '/' in symbol:
            return symbol
        
        # Handle Binance format (BTCUSDT -> BTC/USDT)
        for base in self.supported_currencies:
            if symbol.startswith(base):
                quote = symbol[len(base):]
                if quote in self.supported_currencies:
                    return f"{base}/{quote}"
        
        return symbol

    def _is_ws_connected(self, ws) -> bool:
        """Check if the WebSocket connection is active and healthy"""
        try:
            if ws is None:
                return False
            
            # Check if WebSocketApp has the sock attribute and it's connected
            if hasattr(ws, 'sock') and ws.sock is not None:
                # Different websocket-client versions have different attributes
                sock = ws.sock
                if hasattr(sock, 'connected') and sock.connected:
                    return True
                if hasattr(sock, '_connected') and sock._connected:
                    return True
            
            # Alternative check for different versions
            if hasattr(ws, 'keep_running') and ws.keep_running:
                return True
                
            return False
        except Exception as e:
            logger.debug(f"WebSocket connection check error: {e}")
            return False
    
    def _build_binance_streams(self, pairs: List[str]) -> List[str]:
        """Build Binance stream names from supported_pairs"""
        streams = []
        for p in pairs:
            # normalize: accept "BTC/USDT" or "BTCUSDT"
            if '/' in p:
                base, quote = p.split('/')
                symbol = f"{base}{quote}"
            else:
                symbol = p
            streams.append(f"{symbol.lower()}@ticker")
        return streams

    def _monitor_websockets(self, interval: float = 5.0):
        """Background monitor that checks health of websocket connections and attempts controlled reconnects"""
        logger.info("WebSocket health monitor started")
        while not self._health_thread_stop.is_set():
            try:
                with self.ws_lock:
                    for key, ws in list(self.ws_connections.items()):
                        # if connection is unhealthy, trigger reconnect flow for parent exchange
                        if not self._is_ws_connected(ws):
                            exchange = key.split('_')[0] if '_' in key else key
                            logger.warning(f"Detected unhealthy WS for {key} (exchange={exchange})")
                            # close and remove if present
                            try:
                                if ws is not None and hasattr(ws, 'close'):
                                    ws.close()
                            except Exception as e:
                                logger.debug(f"Error closing unhealthy ws {key}: {e}")
                            # remove safely
                            if key in self.ws_connections:
                                del self.ws_connections[key]
                            # attempt reconnect for exchange if allowed
                            attempts = self.reconnect_attempts.get(exchange, 0)
                            if self._system_running and attempts < self.max_reconnect_attempts:
                                self.reconnect_attempts[exchange] = attempts + 1
                                delay = min(5 * self.reconnect_attempts[exchange], 30)
                                logger.info(f"Scheduling reconnect for {exchange} in {delay}s (attempt {self.reconnect_attempts[exchange]})")
                                threading.Timer(delay, lambda ex=exchange: self.start_websocket(ex)).start()
                            else:
                                logger.error(f"Max reconnection attempts reached for {exchange} or system stopped")
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in WebSocket health monitor: {e}")
                time.sleep(interval)
        logger.info("WebSocket health monitor stopped")

    def _ensure_health_monitor(self):
        """Ensure the health monitor thread is started/stopped with websockets"""
        if self._health_thread is None or not self._health_thread.is_alive():
            self._health_thread_stop.clear()
            self._health_thread = threading.Thread(target=self._monitor_websockets, name="WS-Health-Monitor", daemon=True)
            self._health_thread.start()

    def start_all_websockets(self):
        """Start WebSocket connections for all supported exchanges"""
        if not WEBSOCKET_AVAILABLE:
            logger.error("WebSocket client not available. Please install: pip install websocket-client")
            return
            
        logger.info("Starting all WebSocket connections")
        self._system_running = True
        # reset reconnect attempts
        for exchange in self.exchanges.keys():
            self.reconnect_attempts[exchange] = 0
            self.start_websocket(exchange)

        # start health monitor
        self._ensure_health_monitor()

    def start_websocket(self, exchange: str):
        """Start WebSocket connection for real-time data"""
        if not WEBSOCKET_AVAILABLE:
            logger.error("WebSocket client not available. Please install: pip install websocket-client")
            # Add sample data when WebSocket is not available
            self.add_sample_prices()
            return

        # Avoid duplicate starts: check prefix presence
        with self.ws_lock:
            running_exchanges = {k.split('_')[0] for k in self.ws_connections.keys()}
        if exchange in running_exchanges:
            logger.info(f"WebSocket already running for {exchange}")
            return

        if exchange not in self.reconnect_attempts:
            self.reconnect_attempts[exchange] = 0

        if exchange == 'binance':
            # use multi-stream URL built from normalized supported pairs
            streams = self._build_binance_streams(self.supported_pairs)
            stream_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
            logger.info(f"Connecting to Binance WebSocket with {len(streams)} streams")
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    price_updates = {}
                    # support multiple formats as before
                    if 'stream' in data and 'data' in data:
                        stream_data = data['data']
                        symbol = self._format_symbol(stream_data.get('s', ''))
                        price = float(stream_data.get('c', 0))
                        price_updates[symbol] = price
                    elif isinstance(data, dict) and 's' in data and 'c' in data:
                        symbol = self._format_symbol(data['s'])
                        price = float(data['c'])
                        price_updates[symbol] = price
                    elif isinstance(data, list):
                        for ticker in data:
                            if 's' in ticker and 'c' in ticker:
                                symbol = self._format_symbol(ticker['s'])
                                price_updates[symbol] = float(ticker['c'])
                    if price_updates:
                        self.update_prices('binance', price_updates)
                except Exception as e:
                    logger.debug(f"Error processing binance message: {e}")

            def on_error(ws, error):
                logger.error(f"WebSocket error for binance: {error}")
                self.is_connected = False

            def on_close(ws, close_status_code, close_msg):
                logger.info(f"WebSocket connection closed for binance ({close_status_code}: {close_msg})")
                self.is_connected = False
                with self.ws_lock:
                    if 'binance' in self.ws_connections:
                        del self.ws_connections['binance']
                # reconnect handled by monitor

            def on_open(ws):
                logger.info("WebSocket connected to binance")
                self.is_connected = True
                self.reconnect_attempts['binance'] = 0

            try:
                ws = websocket.WebSocketApp(
                    stream_url,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                    on_open=on_open
                )
                with self.ws_lock:
                    self.ws_connections['binance'] = ws
                thread = threading.Thread(target=ws.run_forever, name="WS-binance", daemon=True)
                thread.start()
                # ensure health monitor
                self._ensure_health_monitor()
            except Exception as e:
                logger.error(f"Failed to start WebSocket for binance: {e}")
                self.is_connected = False

        elif exchange == 'kraken':
            # Keep placeholder but start monitor too
            logger.info("Kraken WS not implemented; skipping for now")
            self._ensure_health_monitor()
        else:
            logger.error(f"Unsupported exchange for WebSocket: {exchange}")

    def stop_websocket(self, exchange: str = None):
        """Stop WebSocket connections"""
        # stop health monitor
        self._health_thread_stop.set()
        try:
            if self._health_thread and self._health_thread.is_alive():
                self._health_thread.join(timeout=2)
        except Exception:
            pass

        with self.ws_lock:
            try:
                if exchange:
                    keys_to_close = [k for k in list(self.ws_connections.keys())
                                     if k == exchange or k.startswith(f"{exchange}_")]
                    for key in keys_to_close:
                        ws = self.ws_connections.get(key)
                        try:
                            if ws is not None and hasattr(ws, 'close'):
                                try:
                                    ws.close()
                                except Exception as inner:
                                    logger.debug(f"Error while closing ws {key}: {inner}")
                            logger.info(f"WebSocket connection closed for {key}")
                        except Exception as e:
                            logger.error(f"Error closing WebSocket for {key}: {e}")
                        finally:
                            if key in self.ws_connections:
                                del self.ws_connections[key]
                else:
                    self._system_running = False
                    for key, ws in list(self.ws_connections.items()):
                        try:
                            if ws is not None and hasattr(ws, 'close'):
                                try:
                                    ws.close()
                                except Exception as inner:
                                    logger.debug(f"Error while closing ws {key}: {inner}")
                            logger.info(f"WebSocket connection closed for {key}")
                        except Exception as e:
                            logger.error(f"Error closing WebSocket for {key}: {e}")
                    self.ws_connections = {}
                    self.is_connected = False
                    logger.info("All WebSocket connections stopped")
            except Exception as e:
                logger.error(f"Error stopping websocket(s): {e}")
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get connection status for all exchanges"""
        status = {}
        with self.ws_lock:
            for exchange in self.exchanges.keys():
                # consider any connection key that starts with exchange as connected
                connected = any(k == exchange or k.startswith(f"{exchange}_") for k in self.ws_connections.keys())
                status[exchange] = connected
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
            # Base pairs for triangles
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
            'LINK/BTC': 0.000315,
            'LTC/USDT': 68.0,
            'LTC/BTC': 0.001511,
            'BCH/USDT': 240.0,
            'BCH/BTC': 0.005333,
            'XRP/USDT': 0.52,
            'XRP/BTC': 0.0000115,
            
            # Additional pairs for more triangles
            'BNB/ETH': 0.1185,
            'ADA/ETH': 0.000203,
            'DOT/ETH': 0.002407,
            'LINK/ETH': 0.005259,
        }
        
        self.update_prices('sample', sample_prices)
        logger.info(f"Added {len(sample_prices)} sample prices for testing")
        
        # Log available triangles
        symbols = list(sample_prices.keys())
        logger.info(f"Sample symbols available: {len(symbols)}")

# Global market data manager instance
market_data_manager = MarketDataManager()

# Initialize with sample data if no WebSocket available
if not WEBSOCKET_AVAILABLE:
    logger.info("WebSocket client not available or misconfigured, initializing with sample data")
    market_data_manager.add_sample_prices()