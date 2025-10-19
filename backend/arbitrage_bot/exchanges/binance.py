# backend/arbitrage_bot/exchanges/binance.py
import os
from typing import Dict, List, Tuple
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

    def get_balance(self) -> Dict:
        """Get account balance with enhanced logging"""
        try:
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