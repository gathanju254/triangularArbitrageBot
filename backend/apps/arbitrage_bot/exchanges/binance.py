# backend/arbitrage_bot/exchanges/binance.py
import os
import time
from typing import Dict, List, Tuple
from .base_exchange import BaseExchange
import ccxt
import logging

logger = logging.getLogger(__name__)

class BinanceClient(BaseExchange):
    def __init__(self):
        api_key = os.getenv('BINANCE_API_KEY', '')
        secret_key = os.getenv('BINANCE_SECRET_KEY', '')
        
        # Debug logging to verify environment variables
        logger.info(f"🔑 Binance API Key loaded: {'Yes' if api_key else 'No'}")
        logger.info(f"🔑 Binance Secret Key loaded: {'Yes' if secret_key else 'No'}")
        
        if not api_key or not secret_key:
            logger.error("❌ Binance API keys are missing from environment variables!")
            logger.error("   Please check your .env file and restart the server")
        
        super().__init__('binance', api_key, secret_key)

        # Enhanced time synchronization settings for Kenya/development
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'sandbox': False,
            'enableRateLimit': True,
            'options': {
                'adjustForTimeDifference': True,
                'recvWindow': 60000,  # Increased to 60 seconds for development
                'defaultType': 'spot',
            }
        })

        self.initialized = False
        self.ready_for_trading = False
        
        try:
            # Force time synchronization before loading markets
            self._synchronize_time()
            
            # Load markets
            logger.info("🔌 Loading Binance markets...")
            markets = self.exchange.load_markets()
            logger.info(f"✅ Binance connection successful! Loaded {len(markets)} markets")
            self.initialized = True
            self.ready_for_trading = self.initialized and self.is_authenticated
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Binance client: {e}")
            # Create fallback instance for read-only operations
            try:
                self.exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {'adjustForTimeDifference': True}
                })
            except Exception:
                self.exchange = None
            self.initialized = False
            self.ready_for_trading = False
    
    def _synchronize_time(self):
        """Enhanced time synchronization for Binance with large time differences.

        - Prefer public REST time endpoint.
        - Cap recvWindow to Binance limit (< 60000).
        - If small skew, apply a runtime offset by overriding exchange.milliseconds() so ccxt uses server time.
        - Fail fast for very large skews and ask user to sync OS clock.
        """
        import requests
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"🕒 Synchronizing time with Binance (attempt {attempt + 1})...")

                # Cap recvWindow to Binance allowed max
                recv_window = int(self.exchange.options.get('recvWindow', 60000))
                recv_window = max(1000, min(recv_window, 59999))
                self.exchange.options['recvWindow'] = recv_window

                # Try public endpoint first (avoids signed request issues)
                try:
                    r = requests.get('https://api.binance.com/api/v3/time', timeout=5)
                    r.raise_for_status()
                    server_time = int(r.json().get('serverTime'))
                except Exception:
                    # fallback to ccxt if public endpoint fails
                    server_time = int(self.exchange.fetch_time())

                local_time = int(time.time() * 1000)
                time_diff = int(server_time - local_time)  # ms
                logger.info(f"⏱️ Time sync: server={server_time}, local={local_time}, diff={time_diff}ms")

                # If skew is huge (>30s) require OS time sync
                if abs(time_diff) > 30000:
                    logger.error(f"❌ System clock out of sync by {time_diff/1000:.2f}s. Please sync OS clock (ntp/w32tm).")
                    raise Exception(f"System clock out of sync by {time_diff/1000:.2f}s")

                # Apply adjustment for ccxt and also override milliseconds() to use server offset.
                # This ensures signed requests use server-aligned timestamps even if OS clock is slightly off.
                self.exchange.options['adjustForTimeDifference'] = True
                self.exchange.options['timeDifference'] = time_diff

                # Monkeypatch ccxt timestamp provider to include time_diff offset
                try:
                    self.exchange.milliseconds = lambda: int(time.time() * 1000) + int(time_diff)
                    logger.debug("✅ Overrode exchange.milliseconds() to apply server time offset")
                except Exception as e:
                    logger.debug(f"Could not override milliseconds(): {e}")

                # Quick public call to validate
                self.exchange.fetch_ticker('BTC/USDT')
                logger.info("✅ Time synchronization successful!")
                return

            except ccxt.RequestTimeout as e:
                logger.warning(f"⏱️ Time sync attempt {attempt + 1} timed out: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)

            except Exception as e:
                err_str = str(e)
                logger.warning(f"⏱️ Time sync attempt {attempt + 1} failed: {err_str}")

                # Ensure recvWindow remains compliant
                if 'recvWindow' in err_str or '-1131' in err_str:
                    self.exchange.options['recvWindow'] = 59999
                    logger.info(f"📈 recvWindow capped to {self.exchange.options['recvWindow']}ms")

                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    logger.error("❌ All time synchronization attempts failed")
                    raise

    def _ensure_exchange_available(self):
        """Internal helper to raise a clear error if exchange not ready"""
        if not self.exchange:
            raise Exception("Binance exchange client not available (initialization failed)")
        if not self.initialized:
            raise Exception("Binance client not fully initialized (time sync / markets not loaded)")
        if not self.is_authenticated:
            raise Exception("Binance API keys not configured - cannot perform authenticated trading")

    def get_ticker(self, symbol: str) -> Dict:
        try:
            if not self.exchange:
                raise Exception("Exchange client not available")
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker.get('last'),
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'volume': ticker.get('baseVolume')
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}
    
    def get_all_tickers(self) -> Dict[str, float]:
        try:
            if not self.exchange:
                raise Exception("Exchange client not available")
            tickers = self.exchange.fetch_tickers()
            return {symbol: data.get('last') for symbol, data in tickers.items() if data.get('last') is not None}
        except Exception as e:
            logger.error(f"Error fetching all tickers: {e}")
            return {}
    
    def get_symbols(self) -> List[str]:
        try:
            if not self.exchange:
                raise Exception("Exchange client not available")
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []
    
    def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: float = None) -> Dict:
        try:
            # Ensure we don't attempt to create orders if initialization failed
            if not self.ready_for_trading:
                # Provide helpful debugging hint
                raise Exception("Binance client not ready for trading: either API keys missing or client initialization (time sync / markets) failed")
            
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
            if not self.ready_for_trading:
                raise Exception("Binance client not ready for trading: cannot fetch orders")
            
            return self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error fetching order: {e}")
            raise

    def get_balance(self) -> Dict:
        """Get account balance with enhanced logging"""
        try:
            if not self.exchange:
                logger.warning("Binance client exchange not initialized - cannot fetch balance")
                return {}
            
            if not self.is_authenticated:
                logger.warning("Binance client not authenticated - cannot fetch balance")
                return {}
            
            balance = self.exchange.fetch_balance()
            free_balance = balance.get('free', {})
            total_balance = balance.get('total', {})
            
            # Log important balances
            important_currencies = ['USDT', 'BTC', 'ETH', 'BNB', 'USD']
            balance_summary = {}
            
            for currency in important_currencies:
                free = free_balance.get(currency, 0)
                total = total_balance.get(currency, 0)
                if free > 0 or total > 0:
                    balance_summary[currency] = {
                        'free': free,
                        'total': total
                    }
                    logger.info(f"💰 Binance {currency} Balance: Free={free:.8f}, Total={total:.8f}")
            
            logger.info(f"📊 Binance balance summary: {len(balance_summary)} currencies with balance")
            return balance_summary
            
        except Exception as e:
            logger.error(f"❌ Error fetching Binance balance: {e}")
            return {}

    def check_sufficient_balance(self, currency: str, required_amount: float) -> Tuple[bool, float, str]:
        """Check if sufficient balance exists for a trade"""
        try:
            balance = self.get_balance()
            free_balance = 0
            
            # Convert required amount if needed
            if currency.upper() != 'USDT':
                # Would need conversion logic here
                logger.warning(f"Balance check for non-USDT currency {currency} not fully implemented")
                return True, 0, "Assuming sufficient balance for non-USDT"
            
            free_balance = balance.get('USDT', {}).get('free', 0)
            
            if free_balance >= required_amount:
                return True, free_balance, f"Sufficient balance: ${free_balance:.2f} available"
            else:
                return False, free_balance, f"Insufficient balance: ${free_balance:.2f} available, ${required_amount:.2f} required"
                
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return False, 0, f"Balance check failed: {str(e)}"

    def get_account_balance(self) -> Dict:
        """Get detailed account balance with all currencies"""
        try:
            if not self.is_authenticated:
                logger.warning("Binance client not authenticated - cannot fetch balance")
                return {'error': 'Binance API not authenticated'}
            
            if not self.exchange:
                return {'error': 'Binance exchange not initialized'}
            
            logger.info("📊 Fetching Binance account balance...")
            balance = self.exchange.fetch_balance()
            free_balance = balance.get('free', {})
            total_balance = balance.get('total', {})
            used_balance = balance.get('used', {})
            
            # Format balance for all currencies with non-zero amounts
            balance_summary = {}
            total_usd_value = 0.0
            
            for currency, free_amount in free_balance.items():
                free = float(free_amount or 0)
                total = float(total_balance.get(currency, 0))
                used = float(used_balance.get(currency, 0))
                
                if free > 0 or total > 0:
                    # Try to get current price for USD conversion
                    usd_value = 0.0
                    if currency != 'USDT' and currency != 'USD' and currency != 'BUSD':
                        try:
                            # Try common trading pairs
                            symbol = f"{currency}/USDT"
                            ticker = self.get_ticker(symbol)
                            if ticker and 'last' in ticker:
                                usd_value = total * float(ticker['last'])
                        except Exception:
                            try:
                                symbol = f"{currency}/BUSD"
                                ticker = self.get_ticker(symbol)
                                if ticker and 'last' in ticker:
                                    usd_value = total * float(ticker['last'])
                            except Exception:
                                pass
                    elif currency in ['USDT', 'USD', 'BUSD']:
                        usd_value = total
                    
                    total_usd_value += usd_value
                    
                    balance_summary[currency] = {
                        'free': free,
                        'total': total,
                        'used': used,
                        'usd_value': usd_value
                    }
            
            # Sort by USD value descending
            sorted_balance = dict(sorted(
                balance_summary.items(), 
                key=lambda x: x[1]['usd_value'], 
                reverse=True
            ))
            
            logger.info(f"💰 Binance balance fetched: ${total_usd_value:.2f} total value across {len(sorted_balance)} currencies")
            
            return {
                'balances': sorted_balance,
                'total_usd_value': total_usd_value,
                'timestamp': time.time(),
                'authenticated': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching Binance balance: {e}")
            return {'error': str(e), 'authenticated': False}

    def get_exchange_balance(self) -> Dict:
        """Alias for get_account_balance for compatibility with risk manager"""
        return self.get_account_balance()

    def test_connection(self) -> Tuple[bool, str]:
        """Test exchange connection and authentication"""
        try:
            if not self.exchange:
                return False, "Exchange not initialized"
            
            # Test by fetching balance (this will return clear error if not initialized/auth)
            balance = self.get_account_balance()
            if 'error' in balance:
                return False, f"Authentication/initialization failed: {balance.get('error')}"
            
            return True, f"Connection successful - Total balance: ${balance.get('total_usd_value', 0):.2f}"
            
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    def get_trading_fees(self) -> Dict:
        """Get trading fees for the account"""
        try:
            if not self.is_authenticated or not self.initialized:
                return {'error': 'Not authenticated or client not initialized'}
            
            fees = self.exchange.fetch_transaction_fees()
            return fees
            
        except Exception as e:
            logger.error(f"Error fetching trading fees: {e}")
            return {'error': str(e)}

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            if not self.is_authenticated or not self.initialized:
                return []
            
            if symbol:
                orders = self.exchange.fetch_open_orders(symbol)
            else:
                orders = self.exchange.fetch_open_orders()
            
            return orders
            
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order"""
        try:
            if not self.is_authenticated or not self.initialized:
                return False
            
            result = self.exchange.cancel_order(order_id, symbol)
            return True
            
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return False

    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a symbol"""
        try:
            if not self.is_authenticated or not self.initialized:
                return []
            trades = self.exchange.fetch_my_trades(symbol, limit=limit)
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching recent trades for {symbol}: {e}")
            return []

    def get_deposit_address(self, currency: str) -> Dict:
        """Get deposit address for a currency"""
        try:
            if not self.is_authenticated or not self.initialized:
                return {'error': 'Not authenticated or client not initialized'}
            
            address = self.exchange.fetch_deposit_address(currency)
            return address
            
        except Exception as e:
            logger.error(f"Error fetching deposit address for {currency}: {e}")
            return {'error': str(e)}