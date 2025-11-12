# backend/apps/exchanges/api_key_integration.py
# backend/apps/exchanges/api_key_integration.py

import logging
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.utils import timezone

from apps.users.models import APIKey, User
from apps.users.services import APIKeyService
from .models import Exchange

logger = logging.getLogger(__name__)


class ExchangeAPIKeyIntegration:
    """
    Enhanced integration between exchanges app and users API key models.
    Provides seamless API key retrieval for exchange operations.
    """
    
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_PREFIX = "exchange_api_integration"
    
    @staticmethod
    def _get_cache_key(key_suffix: str) -> str:
        """Generate cache key with prefix"""
        return f"{ExchangeAPIKeyIntegration.CACHE_PREFIX}:{key_suffix}"
    
    @staticmethod
    def get_exchange_api_keys(user: User, exchange_code: str) -> Optional[Dict[str, Any]]:
        """
        Get API keys for a specific exchange from user's stored API keys.
        
        Args:
            user: User object
            exchange_code: Exchange code (e.g., 'binance', 'okx')
            
        Returns:
            Dictionary with API keys or None if not found
        """
        cache_key = ExchangeAPIKeyIntegration._get_cache_key(
            f"user_{user.id}_exchange_{exchange_code}_keys"
        )
        
        # Try cache first
        cached_keys = cache.get(cache_key)
        if cached_keys is not None:
            logger.debug(f"Cache hit for {exchange_code} API keys (user: {user.id})")
            return cached_keys
        
        try:
            # Get active and validated API key for this exchange
            api_key_instance = APIKey.objects.filter(
                user=user,
                exchange=exchange_code,
                is_active=True,
                is_validated=True
            ).first()
            
            if not api_key_instance:
                logger.warning(f"No active API key found for {exchange_code} (user: {user.username})")
                return None
            
            # Get decrypted values using the APIKeyService
            decrypted_data = APIKeyService.get_api_key_with_decrypted_values(
                api_key_id=api_key_instance.id,
                user=user,
                use_cache=True
            )
            
            if not decrypted_data:
                logger.error(f"Failed to decrypt API key for {exchange_code}")
                return None
            
            # Format for exchange connectors
            api_keys = {
                'api_key': decrypted_data.get('api_key'),
                'secret_key': decrypted_data.get('secret_key'),
                'passphrase': decrypted_data.get('passphrase'),
                'api_key_id': api_key_instance.id,
                'exchange': exchange_code,
                'permissions': api_key_instance.permissions,
                'is_validated': api_key_instance.is_validated,
                'last_validated': api_key_instance.last_validated,
                'label': api_key_instance.label
            }
            
            # Cache the result
            cache.set(cache_key, api_keys, ExchangeAPIKeyIntegration.CACHE_TIMEOUT)
            
            logger.info(f"✅ Retrieved API keys for {exchange_code} (user: {user.username})")
            return api_keys
            
        except Exception as e:
            logger.error(f"❌ Failed to get API keys for {exchange_code}: {e}")
            return None
    
    @staticmethod
    def get_all_exchange_api_keys(user: User) -> Dict[str, Dict[str, Any]]:
        """
        Get all exchange API keys for a user.
        
        Args:
            user: User object
            
        Returns:
            Dictionary mapping exchange codes to API key data
        """
        cache_key = ExchangeAPIKeyIntegration._get_cache_key(f"user_{user.id}_all_exchange_keys")
        
        # Try cache first
        cached_keys = cache.get(cache_key)
        if cached_keys is not None:
            logger.debug(f"Cache hit for all exchange API keys (user: {user.id})")
            return cached_keys
        
        try:
            # Get all active API keys
            api_key_instances = APIKey.objects.filter(
                user=user,
                is_active=True,
                is_validated=True
            )
            
            all_keys = {}
            
            for api_key_instance in api_key_instances:
                try:
                    decrypted_data = APIKeyService.get_api_key_with_decrypted_values(
                        api_key_id=api_key_instance.id,
                        user=user,
                        use_cache=False  # Don't use cache in loop
                    )
                    
                    if decrypted_data:
                        all_keys[api_key_instance.exchange] = {
                            'api_key': decrypted_data.get('api_key'),
                            'secret_key': decrypted_data.get('secret_key'),
                            'passphrase': decrypted_data.get('passphrase'),
                            'api_key_id': api_key_instance.id,
                            'permissions': api_key_instance.permissions,
                            'label': api_key_instance.label,
                            'is_validated': api_key_instance.is_validated,
                            'last_validated': api_key_instance.last_validated
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to process API key for {api_key_instance.exchange}: {e}")
                    continue
            
            # Cache the results
            cache.set(cache_key, all_keys, ExchangeAPIKeyIntegration.CACHE_TIMEOUT)
            
            logger.info(f"✅ Retrieved API keys for {len(all_keys)} exchanges (user: {user.username})")
            return all_keys
            
        except Exception as e:
            logger.error(f"❌ Failed to get all exchange API keys: {e}")
            return {}
    
    @staticmethod
    def create_exchange_connector(user: User, exchange_code: str, **kwargs):
        """
        Create an exchange connector with user's API keys.
        
        Args:
            user: User object
            exchange_code: Exchange code
            **kwargs: Additional arguments for connector
            
        Returns:
            Exchange connector instance or None
        """
        try:
            # Get API keys from database
            api_keys = ExchangeAPIKeyIntegration.get_exchange_api_keys(user, exchange_code)
            
            if not api_keys:
                logger.warning(f"No API keys found for {exchange_code}, creating public connector")
                # Create public connector without authentication
                return ExchangeAPIKeyIntegration._create_public_connector(exchange_code, **kwargs)
            
            # Create authenticated connector
            connector_class = ExchangeAPIKeyIntegration._get_connector_class(exchange_code)
            if not connector_class:
                logger.error(f"Unsupported exchange: {exchange_code}")
                return None
            
            # Prepare connector arguments
            connector_args = {
                'api_key': api_keys['api_key'],
                'api_secret': api_keys['secret_key'],
            }
            
            # Add passphrase for exchanges that require it
            if api_keys.get('passphrase'):
                connector_args['passphrase'] = api_keys['passphrase']
            
            # Add any additional kwargs
            connector_args.update(kwargs)
            
            # Create connector instance
            connector = connector_class(**connector_args)
            
            logger.info(f"✅ Created authenticated connector for {exchange_code} (user: {user.username})")
            return connector
            
        except Exception as e:
            logger.error(f"❌ Failed to create connector for {exchange_code}: {e}")
            return None
    
    @staticmethod
    def _create_public_connector(exchange_code: str, **kwargs):
        """
        Create a public (non-authenticated) exchange connector.
        """
        try:
            connector_class = ExchangeAPIKeyIntegration._get_connector_class(exchange_code)
            if not connector_class:
                return None
            
            # Create connector without API keys
            connector = connector_class(**kwargs)
            logger.info(f"✅ Created public connector for {exchange_code}")
            return connector
            
        except Exception as e:
            logger.error(f"❌ Failed to create public connector for {exchange_code}: {e}")
            return None
    
    @staticmethod
    def _get_connector_class(exchange_code: str):
        """
        Get the connector class for an exchange.
        """
        connector_map = {
            'binance': 'apps.exchanges.connectors.binance.BinanceConnector',
            'okx': 'apps.exchanges.connectors.okx.OkxConnector',
            'coinbase': 'apps.exchanges.connectors.coinbase.CoinbaseConnector',
            'kraken': 'apps.exchanges.connectors.kraken.KrakenConnector',
            'kucoin': 'apps.exchanges.connectors.kucoin.KucoinConnector',
            'huobi': 'apps.exchanges.connectors.huobi.HuobiConnector',
        }
        
        connector_path = connector_map.get(exchange_code.lower())
        if not connector_path:
            return None
        
        try:
            # Dynamic import
            module_path, class_name = connector_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            connector_class = getattr(module, class_name)
            return connector_class
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import connector class for {exchange_code}: {e}")
            return None
    
    @staticmethod
    def validate_exchange_connection(user: User, exchange_code: str) -> Dict[str, Any]:
        """
        Validate exchange connection using user's API keys.
        
        Args:
            user: User object
            exchange_code: Exchange code
            
        Returns:
            Dictionary with validation results
        """
        try:
            connector = ExchangeAPIKeyIntegration.create_exchange_connector(user, exchange_code)
            if not connector:
                return {
                    'connected': False,
                    'error': 'Failed to create connector',
                    'exchange': exchange_code,
                    'timestamp': timezone.now().isoformat()
                }
            
            # Test connection by getting exchange status
            status = connector.get_exchange_status()
            
            # If we have API keys, also test authenticated endpoints
            api_keys = ExchangeAPIKeyIntegration.get_exchange_api_keys(user, exchange_code)
            balance_access = False
            trading_enabled = False
            
            if api_keys and connector.api_key:
                try:
                    # Test balance access
                    balance = connector.get_balance()
                    balance_access = bool(balance and len(balance) > 0)
                    
                    # Test trading permissions (non-destructive)
                    trading_enabled = True  # Simplified - would need actual permission check
                    
                except Exception as e:
                    logger.warning(f"Authenticated test failed for {exchange_code}: {e}")
            
            return {
                'connected': status.get('is_online', False),
                'exchange': exchange_code,
                'authenticated': bool(api_keys),
                'balance_access': balance_access,
                'trading_enabled': trading_enabled,
                'status_info': status,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Connection validation failed for {exchange_code}: {e}")
            return {
                'connected': False,
                'error': str(e),
                'exchange': exchange_code,
                'timestamp': timezone.now().isoformat()
            }
    
    @staticmethod
    def get_user_exchanges_with_keys(user: User) -> List[Dict[str, Any]]:
        """
        Get all exchanges where user has configured API keys.
        
        Args:
            user: User object
            
        Returns:
            List of exchange information with key status
        """
        try:
            # Get all exchanges
            exchanges = Exchange.objects.filter(is_active=True)
            user_api_keys = ExchangeAPIKeyIntegration.get_all_exchange_api_keys(user)
            
            result = []
            
            for exchange in exchanges:
                has_keys = exchange.code in user_api_keys
                keys_data = user_api_keys.get(exchange.code, {})
                
                exchange_info = {
                    'exchange_id': exchange.id,
                    'exchange_name': exchange.name,
                    'exchange_code': exchange.code,
                    'has_api_keys': has_keys,
                    'is_validated': keys_data.get('is_validated', False),
                    'permissions': keys_data.get('permissions', []),
                    'label': keys_data.get('label', ''),
                    'last_validated': keys_data.get('last_validated'),
                    'can_trade': has_keys and 'trade' in keys_data.get('permissions', []),
                    'can_withdraw': has_keys and 'withdraw' in keys_data.get('permissions', [])
                }
                
                result.append(exchange_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user exchanges with keys: {e}")
            return []
    
    @staticmethod
    def clear_api_key_cache(user: User, exchange_code: str = None):
        """
        Clear API key cache for a user.
        
        Args:
            user: User object
            exchange_code: Specific exchange to clear (None for all)
        """
        try:
            cache_keys_to_clear = []
            
            if exchange_code:
                cache_keys_to_clear.extend([
                    ExchangeAPIKeyIntegration._get_cache_key(f"user_{user.id}_exchange_{exchange_code}_keys"),
                ])
            else:
                cache_keys_to_clear.extend([
                    ExchangeAPIKeyIntegration._get_cache_key(f"user_{user.id}_all_exchange_keys"),
                ])
                # Clear individual exchange caches
                user_exchanges = APIKey.objects.filter(user=user).values_list('exchange', flat=True)
                for user_exchange in user_exchanges:
                    cache_keys_to_clear.append(
                        ExchangeAPIKeyIntegration._get_cache_key(f"user_{user.id}_exchange_{user_exchange}_keys")
                    )
            
            cache.delete_many(cache_keys_to_clear)
            logger.info(f"✅ Cleared API key cache for {user.username}" + 
                       f" (exchange: {exchange_code})" if exchange_code else "")
            
        except Exception as e:
            logger.error(f"❌ Failed to clear API key cache: {e}")


# Global instance for easy access
exchange_api_integration = ExchangeAPIKeyIntegration()