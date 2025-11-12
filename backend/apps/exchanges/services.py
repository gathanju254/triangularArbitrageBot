# backend/apps/exchanges/services.py
import logging
import time
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Exchange, MarketData, ExchangeCredentials
from .connectors.binance import BinanceConnector
from .connectors.coinbase import CoinbaseConnector
from .connectors.kraken import KrakenConnector
from .connectors.kucoin import KucoinConnector
from .connectors.okx import OkxConnector
from .connectors.huobi import HuobiConnector
from core.exceptions import ExchangeConnectionError

logger = logging.getLogger(__name__)

User = get_user_model()

class ExchangeService:
    """Service for exchange operations"""
    
    def __init__(self, exchange_id: int, credentials: ExchangeCredentials = None, user: Optional[User] = None):
        """
        exchange_id: database id for Exchange
        credentials: optional ExchangeCredentials instance
        user: optional Django user - if provided and credentials is None,
              the service will try to find active credentials for that user & exchange.
        """
        self.exchange_id = exchange_id
        self.credentials = credentials
        self.user = user
        self.exchange = Exchange.objects.get(id=exchange_id)

        # If credentials not provided but a user is, attempt to load user's active credentials
        if self.credentials is None and self.user is not None:
            try:
                self.credentials = ExchangeCredentials.objects.filter(
                    user=self.user,
                    exchange=self.exchange,
                    is_active=True
                ).first()
            except Exception as e:
                logger.debug(f"No ExchangeCredentials found for user {getattr(self.user, 'username', self.user)} and exchange {self.exchange}: {e}")

        self.connector = self._get_connector()
    
    def _get_connector(self):
        """Get appropriate connector for the exchange"""
        connector_map = {
            'binance': BinanceConnector,
            'coinbase': CoinbaseConnector,
            'kraken': KrakenConnector,
            'kucoin': KucoinConnector,
            'okx': OkxConnector,
            'huobi': HuobiConnector,
        }
        
        connector_class = connector_map.get(self.exchange.code.lower())
        if not connector_class:
            raise ExchangeConnectionError(f"Unsupported exchange: {self.exchange.code}")
        
        # Initialize connector with credentials if available
        api_key = None
        api_secret = None
        passphrase = None
        
        if self.credentials and self.credentials.api_key:
            api_key = self.credentials.api_key.key
            api_secret = self.credentials.api_key.get_decrypted_secret()
            # For exchanges like OKX and Coinbase that require passphrase
            passphrase = getattr(self.credentials.api_key, 'passphrase', None)
        
        # Special handling for exchanges that require passphrase
        if self.exchange.code.lower() in ['okx', 'coinbase', 'kucoin']:
            return connector_class(api_key, api_secret, passphrase)
        
        return connector_class(api_key, api_secret)

    def test_api_key_connection(self, exchange: str, api_key: str, secret_key: str, passphrase: str = None) -> Dict[str, Any]:
        """
        Test API key connectivity and permissions with comprehensive validation.

        Returns a dict with connectivity and permission details.
        """
        try:
            connector = self._get_connector_for_validation(exchange, api_key, secret_key, passphrase)

            validation_results = {
                'connected': False,
                'exchange': exchange,
                'permissions': [],
                'account_type': 'unknown',
                'balance_access': False,
                'trading_enabled': False,
                'withdrawal_enabled': False,
                'rate_limits': {},
                'error': None,
                'timestamp': timezone.now().isoformat()
            }

            # Test 1: Basic connectivity & balance/account access
            try:
                if exchange.lower() in ['binance', 'okx', 'kucoin', 'huobi', 'kraken']:
                    balances = connector.get_balance()
                    validation_results['connected'] = True
                    validation_results['balance_access'] = True
                    validation_results['account_type'] = 'spot'
                elif exchange.lower() in ['coinbase']:
                    # coinbase connector may expose accounts
                    if hasattr(connector, 'get_accounts'):
                        accounts = connector.get_accounts()
                        validation_results['connected'] = True
                        validation_results['balance_access'] = True
                        validation_results['account_type'] = 'spot'
                    else:
                        validation_results['connected'] = True
                else:
                    # fallback: try a lightweight status call
                    if hasattr(connector, 'get_exchange_status'):
                        connector.get_exchange_status()
                        validation_results['connected'] = True

            except Exception as e:
                validation_results['error'] = f"Authentication failed: {str(e)}"
                logger.debug(f"API key validation failed at auth step for {exchange}: {e}")
                return validation_results

            # Test 2: Trading permission (best-effort, non-destructive)
            try:
                if exchange.lower() == 'binance' and hasattr(connector, 'get_account_status'):
                    acct = connector.get_account_status()
                    validation_results['trading_enabled'] = bool(acct.get('canTrade', False))
                elif exchange.lower() == 'okx':
                    # If balance was accessible, trading likely possible
                    validation_results['trading_enabled'] = True
                else:
                    # Try checking for open orders or permissions
                    if hasattr(connector, 'get_open_orders'):
                        _ = connector.get_open_orders()  # non-destructive
                        validation_results['trading_enabled'] = True
            except Exception as e:
                logger.debug(f"Non-fatal trading permission check failed for {exchange}: {e}")
                validation_results['trading_enabled'] = False

            # Test 3: Permissions discovery
            try:
                permissions = self._check_exchange_permissions(connector, exchange)
                validation_results['permissions'] = permissions
            except Exception:
                validation_results['permissions'] = ['read']

            # Test 4: Rate limit / latency quick check
            try:
                rate_limits = self._test_rate_limits(connector, exchange)
                validation_results['rate_limits'] = rate_limits
            except Exception:
                # ignore rate limit errors
                logger.debug(f"Rate limit test skipped/failed for {exchange}")

            return validation_results

        except Exception as e:
            logger.error(f"Validation failed for API key on {exchange}: {e}")
            return {
                'connected': False,
                'exchange': exchange,
                'error': f"Validation failed: {str(e)}",
                'timestamp': timezone.now().isoformat()
            }

    def _get_connector_for_validation(self, exchange: str, api_key: str, secret_key: str, passphrase: str = None):
        """Create a connector instance for validation using provided credentials."""
        connector_map = {
            'binance': BinanceConnector,
            'coinbase': CoinbaseConnector,
            'kraken': KrakenConnector,
            'kucoin': KucoinConnector,
            'okx': OkxConnector,
            'huobi': HuobiConnector,
        }
        ex = exchange.lower()
        connector_class = connector_map.get(ex)
        if not connector_class:
            raise ExchangeConnectionError(f"Unsupported exchange for validation: {exchange}")

        # Use passphrase arg for exchanges that need it
        if ex in ['okx', 'coinbase', 'kucoin']:
            return connector_class(api_key, secret_key, passphrase)
        return connector_class(api_key, secret_key)

    def _check_exchange_permissions(self, connector, exchange: str) -> List[str]:
        """Best-effort discovery of permissions available for the provided connector."""
        perms = []
        try:
            # common method names that connectors may implement
            if hasattr(connector, 'get_permissions'):
                p = connector.get_permissions()
                if isinstance(p, list):
                    perms = p
            elif hasattr(connector, 'get_account_status'):
                acct = connector.get_account_status()
                # Map common flags to permission names
                if acct.get('canTrade'):
                    perms.append('trade')
                if acct.get('canWithdraw'):
                    perms.append('withdraw')
                if acct.get('canDeposit') or acct.get('canView'):
                    perms.append('read')
            else:
                # Fallback: presence of balance access implies read
                perms = ['read']
        except Exception as e:
            logger.debug(f"Permission discovery failed for {exchange}: {e}")
            perms = ['read']
        return perms

    def _test_rate_limits(self, connector, exchange: str) -> Dict[str, Any]:
        """Quick non-destructive latency/rate check to estimate response times."""
        result = {'sample_calls': 0, 'avg_ms': None, 'errors': []}
        samples = 2
        timings = []
        for i in range(samples):
            try:
                start = time.time()
                # Try lightweight endpoint in order of preference
                if hasattr(connector, 'get_ticker'):
                    connector.get_ticker('BTC/USDT')
                elif hasattr(connector, 'get_exchange_status'):
                    connector.get_exchange_status()
                else:
                    # no lightweight call available
                    break
                elapsed = (time.time() - start) * 1000.0
                timings.append(elapsed)
                result['sample_calls'] += 1
            except Exception as e:
                result['errors'].append(str(e))
                logger.debug(f"Rate limit probe error for {exchange}: {e}")
                break
        if timings:
            result['avg_ms'] = sum(timings) / len(timings)
        return result
    
    def get_exchange_status(self) -> Dict[str, Any]:
        """Get exchange status"""
        cache_key = f"exchange_status_{self.exchange_id}"
        cached_status = cache.get(cache_key)
        
        if cached_status:
            return cached_status
        
        try:
            status = self.connector.get_exchange_status()
            status['exchange'] = self.exchange
            
            # Cache for 1 minute
            cache.set(cache_key, status, 60)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get status for {self.exchange.name}: {str(e)}")
            return {
                'exchange': self.exchange,
                'is_online': False,
                'last_checked': timezone.now(),
                'response_time_ms': 0,
                'maintenance_mode': False,
                'message': str(e)
            }
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for a symbol"""
        cache_key = f"ticker_{self.exchange_id}_{symbol}"
        cached_ticker = cache.get(cache_key)
        
        if cached_ticker:
            return cached_ticker
        
        try:
            ticker = self.connector.get_ticker(symbol)
            
            # Cache for 5 seconds
            cache.set(cache_key, ticker, 5)
            
            return ticker
            
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol} on {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get ticker: {str(e)}")
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a symbol"""
        cache_key = f"orderbook_{self.exchange_id}_{symbol}_{limit}"
        cached_orderbook = cache.get(cache_key)
        
        if cached_orderbook:
            return cached_orderbook
        
        try:
            orderbook = self.connector.get_order_book(symbol, limit)
            
            # Cache for 2 seconds
            cache.set(cache_key, orderbook, 2)
            
            return orderbook
            
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol} on {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get order book: {str(e)}")
    
    def get_balance(self, credentials: ExchangeCredentials = None) -> Dict[str, Any]:
        """Get account balance"""
        if not self.connector.api_key:
            if credentials:
                # Create new connector with credentials
                self.credentials = credentials
                self.connector = self._get_connector()
            else:
                raise ExchangeConnectionError("API credentials required for balance check")
        
        try:
            balances = self.connector.get_balance()
            
            # Calculate total balance in USD (simplified)
            total_balance_usd = Decimal('0.00')
            # This would require price data for conversion
            
            return {
                'exchange': self.exchange,
                'balances': balances,
                'total_balance_usd': total_balance_usd,
                'last_updated': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance from {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get balance: {str(e)}")
    
    def place_order(self, symbol: str, side: str, order_type: str, 
                   amount: Decimal, price: Decimal = None, 
                   client_order_id: str = None) -> Dict[str, Any]:
        """Place a new order"""
        if not self.connector.api_key:
            raise ExchangeConnectionError("API credentials required for trading")
        
        try:
            order_result = self.connector.place_order(
                symbol, side, order_type, amount, price, client_order_id
            )
            
            logger.info(f"Order placed on {self.exchange.name}: {order_result['id']}")
            return order_result
            
        except Exception as e:
            logger.error(f"Failed to place order on {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to place order: {str(e)}")
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        if not self.connector.api_key:
            raise ExchangeConnectionError("API credentials required for order cancellation")
        
        try:
            success = self.connector.cancel_order(order_id, symbol)
            
            if success:
                logger.info(f"Order {order_id} cancelled on {self.exchange.name}")
            else:
                logger.warning(f"Failed to cancel order {order_id} on {self.exchange.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id} on {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to cancel order: {str(e)}")
    
    def get_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get order status"""
        if not self.connector.api_key:
            raise ExchangeConnectionError("API credentials required for order status")
        
        try:
            order_info = self.connector.get_order(order_id, symbol)
            return order_info
            
        except Exception as e:
            logger.error(f"Failed to get order {order_id} from {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get order: {str(e)}")
    
    def get_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs"""
        cache_key = f"trading_pairs_{self.exchange_id}"
        cached_pairs = cache.get(cache_key)
        
        if cached_pairs:
            return cached_pairs
        
        try:
            pairs = self.connector.get_trading_pairs()
            
            # Cache for 1 hour
            cache.set(cache_key, pairs, 3600)
            
            return pairs
            
        except Exception as e:
            logger.error(f"Failed to get trading pairs from {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get trading pairs: {str(e)}")
    
    def validate_credentials(self) -> bool:
        """Validate API credentials"""
        try:
            return self.connector.validate_credentials()
        except Exception as e:
            logger.error(f"Credential validation failed for {self.exchange.name}: {str(e)}")
            return False
    
    def get_funding_rate(self, symbol: str = None) -> Dict[str, Any]:
        """Get funding rates (for perpetual contracts)"""
        try:
            return self.connector.get_funding_rate(symbol)
        except Exception as e:
            logger.error(f"Failed to get funding rate from {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get funding rate: {str(e)}")
    
    def get_leverage_tiers(self, symbol: str = None) -> Dict[str, Any]:
        """Get leverage tiers (for margin trading)"""
        try:
            return self.connector.get_leverage_tiers(symbol)
        except Exception as e:
            logger.error(f"Failed to get leverage tiers from {self.exchange.name}: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get leverage tiers: {str(e)}")


class MarketDataService:
    """Service for market data operations"""
    
    @staticmethod
    def update_market_data() -> None:
        """Update market data for all active exchanges"""
        active_exchanges = Exchange.objects.filter(is_active=True)
        
        for exchange in active_exchanges:
            try:
                MarketDataService._update_exchange_market_data(exchange)
            except Exception as e:
                logger.error(f"Failed to update market data for {exchange.name}: {str(e)}")
    
    @staticmethod
    def _update_exchange_market_data(exchange: Exchange) -> None:
        """Update market data for a specific exchange"""
        exchange_service = ExchangeService(exchange.id)
        
        # Get supported pairs (first 10 for demo)
        supported_pairs = exchange.supported_pairs[:10] if exchange.supported_pairs else ['BTC/USDT', 'ETH/USDT']
        
        for symbol in supported_pairs:
            try:
                ticker = exchange_service.get_ticker(symbol)
                
                # Create or update market data
                MarketData.objects.update_or_create(
                    exchange=exchange,
                    symbol=symbol,
                    timestamp=ticker['timestamp'],
                    defaults={
                        'bid_price': ticker['bid_price'],
                        'ask_price': ticker['ask_price'],
                        'last_price': ticker['last_price'],
                        'volume_24h': ticker['volume_24h'],
                        'spread': ticker['spread'],
                        'is_fresh': True
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to update {symbol} on {exchange.name}: {str(e)}")
    
    @staticmethod
    def get_ticker_data(symbol: str, exchange_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get ticker data for a symbol across exchanges"""
        tickers = []
        
        if exchange_id:
            exchanges = Exchange.objects.filter(id=exchange_id, is_active=True)
        else:
            exchanges = Exchange.objects.filter(is_active=True)
        
        for exchange in exchanges:
            try:
                exchange_service = ExchangeService(exchange.id)
                ticker = exchange_service.get_ticker(symbol)
                tickers.append(ticker)
            except Exception as e:
                # Skip exchanges that fail
                continue
        
        return tickers
    
    @staticmethod
    def mark_old_data_stale() -> None:
        """Mark market data older than 5 minutes as stale"""
        stale_threshold = timezone.now() - timezone.timedelta(minutes=5)
        MarketData.objects.filter(
            timestamp__lt=stale_threshold,
            is_fresh=True
        ).update(is_fresh=False)
    
    @staticmethod
    def get_arbitrage_opportunities(base_symbol: str = 'USDT') -> List[Dict[str, Any]]:
        """Get arbitrage opportunities across exchanges"""
        opportunities = []
        
        # Get all active exchanges
        exchanges = Exchange.objects.filter(is_active=True)
        
        # Get common trading pairs
        common_pairs = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA']
        
        for pair in common_pairs:
            symbol = f"{pair}/{base_symbol}"
            
            try:
                # Get ticker data for this symbol across all exchanges
                tickers = MarketDataService.get_ticker_data(symbol)
                
                if len(tickers) < 2:
                    continue
                
                # Find best bid and ask across exchanges
                best_bid = max(tickers, key=lambda x: x['bid_price'])
                best_ask = min(tickers, key=lambda x: x['ask_price'])
                
                # Calculate arbitrage opportunity
                if best_bid['bid_price'] > best_ask['ask_price']:
                    spread = ((best_bid['bid_price'] - best_ask['ask_price']) / best_ask['ask_price']) * 100
                    
                    if spread > 0.1:  # Minimum 0.1% spread
                        opportunities.append({
                            'symbol': symbol,
                            'buy_exchange': best_ask['exchange'],
                            'sell_exchange': best_bid['exchange'],
                            'buy_price': best_ask['ask_price'],
                            'sell_price': best_bid['bid_price'],
                            'spread_percentage': spread,
                            'timestamp': timezone.now()
                        })
                        
            except Exception as e:
                logger.error(f"Failed to calculate arbitrage for {symbol}: {str(e)}")
                continue
        
        return sorted(opportunities, key=lambda x: x['spread_percentage'], reverse=True)


class ExchangeDataService:
    """
    Service for managing exchange data operations
    """
    
    @staticmethod
    def get_active_exchanges():
        """Get all active exchanges"""
        return Exchange.objects.filter(is_active=True)
    
    @staticmethod
    def update_market_data(symbol: str, exchange_name: str, data: Dict):
        """Update or create market data for a symbol"""
        try:
            exchange = Exchange.objects.get(name=exchange_name, is_active=True)
            market_data, created = MarketData.objects.update_or_create(
                symbol=symbol,
                exchange=exchange,
                defaults={
                    'bid_price': data.get('bid'),
                    'ask_price': data.get('ask'),
                    'last_price': data.get('last'),
                    'volume': data.get('volume'),
                    'timestamp': data.get('timestamp'),
                }
            )
            return market_data
        except Exchange.DoesNotExist:
            logger.warning(f"Exchange {exchange_name} not found or inactive")
            return None
    
    @staticmethod
    def get_latest_market_data(symbol: str, exchange_name: str = None):
        """Get latest market data for a symbol"""
        try:
            queryset = MarketData.objects.filter(symbol=symbol)
            if exchange_name:
                queryset = queryset.filter(exchange__name=exchange_name)
            
            return queryset.order_by('-timestamp').first()
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    @staticmethod
    def get_arbitrage_opportunities():
        """Get potential arbitrage opportunities across exchanges"""
        # This is a simplified version - implement your actual arbitrage logic here
        opportunities = []
        
        # Get all active exchanges
        exchanges = Exchange.objects.filter(is_active=True)
        
        # For each symbol, compare prices across exchanges
        # This is where you'd implement your specific arbitrage logic
        # For now, return empty list as placeholder
        return opportunities


class ExchangeConnectionService:
    """
    Service for managing exchange connections
    """
    
    @staticmethod
    def test_connection(exchange_name: str) -> bool:
        """Test connection to an exchange"""
        try:
            # Implement actual connection test logic here
            logger.info(f"Testing connection to {exchange_name}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {exchange_name}: {e}")
            return False
    
    @staticmethod
    def get_balance(exchange_name: str) -> Dict:
        """Get balance from exchange"""
        try:
            # Implement actual balance retrieval logic here
            logger.info(f"Getting balance from {exchange_name}")
            return {}
        except Exception as e:
            logger.error(f"Balance retrieval failed for {exchange_name}: {e}")
            return {}


class CredentialsService:
    """Service for exchange credentials management"""
    
    def __init__(self, credentials: ExchangeCredentials):
        self.credentials = credentials
        self.exchange_service = ExchangeService(
            credentials.exchange_id, 
            credentials
        )
    
    def validate_credentials(self) -> bool:
        """Validate exchange credentials"""
        try:
            is_valid = self.exchange_service.validate_credentials()
            
            self.credentials.is_validated = is_valid
            self.credentials.last_validation = timezone.now()
            
            if is_valid:
                self.credentials.validation_message = "Credentials validated successfully"
            else:
                self.credentials.validation_message = "Credentials validation failed"
            
            self.credentials.save()
            
            return is_valid
            
        except Exception as e:
            self.credentials.is_validated = False
            self.credentials.validation_message = str(e)
            self.credentials.last_validation = timezone.now()
            self.credentials.save()
            
            logger.error(f"Credential validation failed for {self.credentials.exchange.name}: {str(e)}")
            return False
    
    def test_trading_permission(self) -> bool:
        """Test if trading is allowed with these credentials"""
        if not self.credentials.is_validated:
            return False
        
        try:
            # Try to place a test order (with minimal amount) or check permissions
            # For now, just check if we can get balance
            self.exchange_service.get_balance()
            return True
            
        except Exception as e:
            logger.error(f"Trading permission test failed: {str(e)}")
            return False
    
    def test_withdrawal_permission(self) -> bool:
        """Test if withdrawal is allowed with these credentials"""
        # This would require attempting a withdrawal or checking account permissions
        # For safety, we'll assume withdrawal is not allowed by default
        return False
    
    def get_account_tier(self) -> str:
        """Get account tier/level information"""
        try:
            # This would vary by exchange - implement in specific connectors
            return self.exchange_service.connector.get_account_tier()
        except Exception as e:
            logger.error(f"Failed to get account tier: {str(e)}")
            return "unknown"


class ExchangeFactory:
    """Factory for creating exchange services"""
    
    @staticmethod
    def get_exchange_by_name(name: str, user: User = None) -> ExchangeService:
        """Get exchange service by name with optional user"""
        try:
            exchange = Exchange.objects.get(name__iexact=name, is_active=True)
            return ExchangeService(exchange.id, user=user)
        except Exchange.DoesNotExist:
            raise ExchangeConnectionError(f"Exchange not found: {name}")
    
    @staticmethod
    def get_exchange_by_code(code: str, user: User = None) -> ExchangeService:
        """Get exchange service by code with optional user"""
        try:
            exchange = Exchange.objects.get(code__iexact=code, is_active=True)
            return ExchangeService(exchange.id, user=user)
        except Exchange.DoesNotExist:
            raise ExchangeConnectionError(f"Exchange not found: {code}")
    
    @staticmethod
    def get_all_active_exchanges(user: User = None) -> List[ExchangeService]:
        """Get services for all active exchanges with optional user"""
        active_exchanges = Exchange.objects.filter(is_active=True)
        return [ExchangeService(exchange.id, user=user) for exchange in active_exchanges]
    
    @staticmethod
    def get_user_exchanges_with_keys(user: User) -> List[ExchangeService]:
        """Get exchange services only for exchanges where user has API keys"""
        # exchange_api_integration should provide a list of exchanges the user has keys for.
        # Implementations may vary; expect list[dict] with keys: exchange_id, exchange_name, has_api_keys
        try:
            from . import exchange_api_integration
        except Exception:
            logger.debug("exchange_api_integration module not available; falling back to ExchangeCredentials lookup")
            exchange_services = []
            creds = ExchangeCredentials.objects.filter(user=user, is_active=True).select_related('exchange')
            seen = set()
            for c in creds:
                if c.exchange_id in seen:
                    continue
                seen.add(c.exchange_id)
                try:
                    exchange_services.append(ExchangeService(c.exchange_id, credentials=c, user=user))
                except Exception as e:
                    logger.error(f"Failed to create service for exchange id {c.exchange_id}: {e}")
            return exchange_services

        user_exchanges = exchange_api_integration.get_user_exchanges_with_keys(user)
        exchange_services = []
        
        for exchange_info in user_exchanges:
            if exchange_info.get('has_api_keys'):
                try:
                    exchange_service = ExchangeService(
                        exchange_info['exchange_id'], 
                        user=user
                    )
                    exchange_services.append(exchange_service)
                except Exception as e:
                    logger.error(f"Failed to create service for {exchange_info.get('exchange_name')}: {e}")
                    continue
        
        return exchange_services


class OKXSpecificService:
    """OKX-specific service methods"""
    
    def __init__(self, exchange_service: ExchangeService):
        self.exchange_service = exchange_service
        if self.exchange_service.exchange.code.lower() != 'okx':
            raise ExchangeConnectionError("This service is only for OKX exchange")
    
    def get_grid_trading_ai_settings(self) -> Dict[str, Any]:
        """Get OKX Grid Trading AI settings"""
        try:
            return self.exchange_service.connector.get_grid_trading_ai_settings()
        except Exception as e:
            logger.error(f"Failed to get OKX Grid Trading AI settings: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get Grid Trading AI settings: {str(e)}")
    
    def get_copy_trading_data(self) -> Dict[str, Any]:
        """Get OKX copy trading data"""
        try:
            return self.exchange_service.connector.get_copy_trading_data()
        except Exception as e:
            logger.error(f"Failed to get OKX copy trading data: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get copy trading data: {str(e)}")
    
    def get_earn_products(self) -> List[Dict[str, Any]]:
        """Get OKX earn products"""
        try:
            return self.exchange_service.connector.get_earn_products()
        except Exception as e:
            logger.error(f"Failed to get OKX earn products: {str(e)}")
            raise ExchangeConnectionError(f"Failed to get earn products: {str(e)}")


# Utility functions
def get_supported_exchanges() -> List[Exchange]:
    """Get list of all supported exchanges"""
    return Exchange.objects.filter(is_active=True)


def get_exchange_by_code(code: str) -> Optional[Exchange]:
    """Get exchange by code"""
    try:
        return Exchange.objects.get(code__iexact=code, is_active=True)
    except Exchange.DoesNotExist:
        return None


def is_exchange_supported(code: str) -> bool:
    """Check if an exchange is supported"""
    return Exchange.objects.filter(code__iexact=code, is_active=True).exists()