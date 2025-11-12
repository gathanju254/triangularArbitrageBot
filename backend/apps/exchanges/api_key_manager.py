# backend/apps/exchanges/api_key_manager.py
# backend/apps/exchanges/api_key_manager.py

import logging
from typing import Dict, Any, Optional, List, Tuple
from django.core.cache import cache
from django.utils import timezone
from django.db import transaction
from apps.users.models import APIKey, User
from apps.users.services import APIKeyService

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Enhanced manager for retrieving and using API keys in trading operations.
    
    Provides comprehensive API key management with caching, validation,
    and exchange-specific functionality.
    """
    
    # Cache settings
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_PREFIX = "api_key_manager"
    
    # Exchange-specific configuration
    EXCHANGE_CONFIGS = {
        'binance': {
            'required_permissions': ['spot', 'margin'],
            'rate_limit_delay': 0.1,
            'max_retries': 3
        },
        'coinbase': {
            'required_permissions': ['wallet', 'trading'],
            'rate_limit_delay': 0.2,
            'max_retries': 2
        },
        'kucoin': {
            'required_permissions': ['general', 'trade'],
            'rate_limit_delay': 0.15,
            'max_retries': 3
        },
        'okx': {
            'required_permissions': ['read', 'trade'],
            'rate_limit_delay': 0.1,
            'max_retries': 3
        },
        'kraken': {
            'required_permissions': ['query', 'trade'],
            'rate_limit_delay': 0.3,
            'max_retries': 2
        }
    }
    
    @staticmethod
    def _get_cache_key(key_suffix: str) -> str:
        """Generate cache key with prefix"""
        return f"{APIKeyManager.CACHE_PREFIX}:{key_suffix}"
    
    @staticmethod
    def _validate_credentials_structure(credentials: Dict[str, Any]) -> bool:
        """
        Validate the structure of credentials dictionary.
        
        Args:
            credentials: Credentials dictionary to validate
            
        Returns:
            bool: True if structure is valid
        """
        required_fields = ['api_key', 'secret_key', 'exchange']
        
        if not credentials:
            return False
        
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                logger.warning(f"Missing required field in credentials: {field}")
                return False
        
        return True
    
    @staticmethod
    def get_exchange_credentials(
        user: User, 
        exchange: str, 
        use_cache: bool = True,
        validate_first: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get decrypted credentials for a specific exchange with enhanced features.
        
        Args:
            user: User object
            exchange: Exchange name
            use_cache: Whether to use cached credentials
            validate_first: Whether to validate credentials before returning
            
        Returns:
            Dictionary with credentials or None if not found/invalid
        """
        cache_key = APIKeyManager._get_cache_key(f"user_{user.id}_exchange_{exchange}_creds")
        
        if use_cache:
            cached_credentials = cache.get(cache_key)
            if cached_credentials is not None:
                logger.debug(f"Cache hit for {exchange} credentials (user: {user.id})")
                return cached_credentials
        
        try:
            # Get the API key instance
            api_key = APIKey.objects.filter(
                user=user, 
                exchange=exchange, 
                is_active=True
            ).first()
            
            if not api_key:
                logger.warning(f"No active API key found for {exchange} (user: {user.username})")
                return None
            
            if validate_first and not api_key.is_validated:
                logger.warning(f"API key for {exchange} is not validated (user: {user.username})")
                return None
            
            # Use the service to get decrypted values
            credentials = APIKeyService.get_api_key_with_decrypted_values(
                api_key_id=api_key.id, 
                user=user,
                use_cache=use_cache
            )
            
            if not APIKeyManager._validate_credentials_structure(credentials):
                logger.error(f"Invalid credentials structure for {exchange}")
                return None
            
            # Add metadata
            credentials.update({
                'api_key_id': api_key.id,
                'is_validated': api_key.is_validated,
                'last_validated': api_key.last_validated.isoformat() if api_key.last_validated else None,
                'exchange_config': APIKeyManager.EXCHANGE_CONFIGS.get(exchange, {})
            })
            
            # Cache the credentials
            if use_cache:
                # Cache for shorter time since it contains sensitive data
                cache.set(cache_key, credentials, 120)  # 2 minutes for sensitive data
            
            logger.info(f"✅ Retrieved credentials for {exchange} (user: {user.username})")
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Failed to get credentials for {exchange}: {e}")
            return None
    
    @staticmethod
    def get_all_active_credentials(
        user: User, 
        use_cache: bool = True,
        only_validated: bool = False
    ) -> Dict[str, Any]:
        """
        Get all active exchange credentials for a user with enhanced filtering.
        
        Args:
            user: User object
            use_cache: Whether to use cached credentials
            only_validated: Whether to return only validated credentials
            
        Returns:
            Dictionary with exchange -> credentials mapping
        """
        cache_key = APIKeyManager._get_cache_key(
            f"user_{user.id}_all_creds_{'validated' if only_validated else 'all'}"
        )
        
        if use_cache:
            cached_credentials = cache.get(cache_key)
            if cached_credentials is not None:
                logger.debug(f"Cache hit for all credentials (user: {user.id})")
                return cached_credentials
        
        try:
            # Build query
            query = APIKey.objects.filter(user=user, is_active=True)
            if only_validated:
                query = query.filter(is_validated=True)
            
            active_api_keys = query.select_related('user')
            credentials = {}
            
            for api_key in active_api_keys:
                try:
                    creds = APIKeyManager.get_exchange_credentials(
                        user=user,
                        exchange=api_key.exchange,
                        use_cache=False,  # Don't use cache in loop to avoid nested caching
                        validate_first=only_validated
                    )
                    
                    if creds:
                        credentials[api_key.exchange] = creds
                        
                except Exception as e:
                    logger.error(f"Failed to get credentials for {api_key.exchange}: {e}")
                    continue
            
            # Cache the results
            if use_cache:
                cache.set(cache_key, credentials, APIKeyManager.CACHE_TIMEOUT)
            
            logger.info(f"✅ Retrieved {len(credentials)} active credentials for {user.username}")
            return credentials
            
        except Exception as e:
            logger.error(f"❌ Failed to get all credentials for {user.username}: {e}")
            return {}
    
    @staticmethod
    def get_credentials_for_trading(
        user: User, 
        exchange: str, 
        symbol: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get credentials specifically for trading operations with additional validation.
        
        Args:
            user: User object
            exchange: Exchange name
            symbol: Trading symbol (optional, for exchange-specific validation)
            
        Returns:
            Dictionary with trading-ready credentials or None
        """
        credentials = APIKeyManager.get_exchange_credentials(
            user=user,
            exchange=exchange,
            validate_first=True  # Always validate for trading
        )
        
        if not credentials:
            return None
        
        # Additional trading-specific validation
        exchange_config = APIKeyManager.EXCHANGE_CONFIGS.get(exchange, {})
        required_permissions = exchange_config.get('required_permissions', [])
        
        # Check if credentials have required permissions (if available in validation result)
        if (credentials.get('permissions') and 
            not all(perm in credentials.get('permissions', []) for perm in required_permissions)):
            logger.warning(f"Insufficient permissions for trading on {exchange}")
            return None
        
        # Add trading-specific metadata
        credentials.update({
            'ready_for_trading': True,
            'retrieved_at': timezone.now().isoformat(),
            'rate_limit_delay': exchange_config.get('rate_limit_delay', 0.1),
            'max_retries': exchange_config.get('max_retries', 3)
        })
        
        logger.info(f"✅ Trading credentials ready for {exchange} (user: {user.username})")
        return credentials
    
    @staticmethod
    def validate_all_credentials(
        user: User, 
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Validate all API key credentials with comprehensive results.
        
        Args:
            user: User object
            force_refresh: Whether to force validation even if recently validated
            
        Returns:
            Dictionary with validation results per exchange
        """
        cache_key = APIKeyManager._get_cache_key(f"user_{user.id}_validation_results")
        
        if not force_refresh:
            cached_results = cache.get(cache_key)
            if cached_results is not None:
                logger.debug(f"Cache hit for validation results (user: {user.id})")
                return cached_results
        
        active_api_keys = APIKey.objects.filter(user=user, is_active=True)
        results = {
            'total_tested': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'errors': [],
            'exchanges': {}
        }
        
        for api_key in active_api_keys:
            try:
                result = APIKeyService.test_api_key_connection(api_key, force_test=force_refresh)
                
                results['exchanges'][api_key.exchange] = {
                    'connected': result.get('connected', False),
                    'api_key_id': api_key.id,
                    'permissions': result.get('permissions', []),
                    'account_type': result.get('account_type', 'unknown'),
                    'error': result.get('error'),
                    'timestamp': result.get('timestamp', timezone.now().isoformat()),
                    'last_validated': api_key.last_validated.isoformat() if api_key.last_validated else None
                }
                
                results['total_tested'] += 1
                if result.get('connected', False):
                    results['valid_count'] += 1
                else:
                    results['invalid_count'] += 1
                    if result.get('error'):
                        results['errors'].append(f"{api_key.exchange}: {result['error']}")
                
            except Exception as e:
                results['exchanges'][api_key.exchange] = {
                    'connected': False,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
                results['total_tested'] += 1
                results['invalid_count'] += 1
                results['errors'].append(f"{api_key.exchange}: {str(e)}")
        
        # Cache validation results
        cache.set(cache_key, results, 600)  # 10 minutes for validation results
        
        logger.info(f"✅ Validated {results['total_tested']} API keys for {user.username} - "
                   f"{results['valid_count']} valid, {results['invalid_count']} invalid")
        
        return results
    
    @staticmethod
    def get_credentials_batch(
        user: User, 
        exchanges: List[str],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get credentials for multiple exchanges in a single batch operation.
        
        Args:
            user: User object
            exchanges: List of exchange names
            use_cache: Whether to use cached credentials
            
        Returns:
            Dictionary with exchange -> credentials mapping
        """
        credentials_batch = {}
        
        for exchange in exchanges:
            try:
                creds = APIKeyManager.get_exchange_credentials(
                    user=user,
                    exchange=exchange,
                    use_cache=use_cache
                )
                
                if creds:
                    credentials_batch[exchange] = creds
                else:
                    credentials_batch[exchange] = {
                        'error': f'No valid credentials found for {exchange}',
                        'available': False
                    }
                    
            except Exception as e:
                credentials_batch[exchange] = {
                    'error': f'Failed to retrieve credentials: {str(e)}',
                    'available': False
                }
        
        logger.info(f"✅ Retrieved credentials batch for {len(credentials_batch)} exchanges")
        return credentials_batch
    
    @staticmethod
    def health_check(user: User) -> Dict[str, Any]:
        """
        Comprehensive health check for user's API keys.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with health status and details
        """
        health_status = {
            'healthy': False,
            'total_api_keys': 0,
            'active_api_keys': 0,
            'validated_api_keys': 0,
            'ready_for_trading': 0,
            'issues': [],
            'exchanges': {}
        }
        
        try:
            # Get all API keys
            all_api_keys = APIKey.objects.filter(user=user)
            health_status['total_api_keys'] = all_api_keys.count()
            
            # Get active API keys
            active_api_keys = all_api_keys.filter(is_active=True)
            health_status['active_api_keys'] = active_api_keys.count()
            
            # Get validated API keys
            validated_api_keys = active_api_keys.filter(is_validated=True)
            health_status['validated_api_keys'] = validated_api_keys.count()
            
            # Check each exchange
            for api_key in active_api_keys:
                exchange_health = {
                    'active': True,
                    'validated': api_key.is_validated,
                    'encrypted': api_key.is_encrypted,
                    'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
                    'last_validated': api_key.last_validated.isoformat() if api_key.last_validated else None,
                    'ready_for_trading': False
                }
                
                # Check if ready for trading
                if api_key.is_validated:
                    trading_creds = APIKeyManager.get_credentials_for_trading(user, api_key.exchange)
                    exchange_health['ready_for_trading'] = trading_creds is not None
                    
                    if exchange_health['ready_for_trading']:
                        health_status['ready_for_trading'] += 1
                
                health_status['exchanges'][api_key.exchange] = exchange_health
            
            # Determine overall health
            if health_status['active_api_keys'] > 0 and health_status['ready_for_trading'] > 0:
                health_status['healthy'] = True
            else:
                if health_status['active_api_keys'] == 0:
                    health_status['issues'].append('No active API keys')
                if health_status['ready_for_trading'] == 0:
                    health_status['issues'].append('No API keys ready for trading')
            
            logger.info(f"✅ Health check completed for {user.username}: {health_status['healthy']}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed for {user.username}: {e}")
            health_status['issues'].append(f'Health check failed: {str(e)}')
        
        return health_status
    
    @staticmethod
    def rotate_credentials_cache(user: User, exchange: str = None) -> bool:
        """
        Rotate (clear) credentials cache for a user.
        
        Args:
            user: User object
            exchange: Specific exchange to clear cache for (None for all)
            
        Returns:
            bool: True if cache was cleared successfully
        """
        try:
            cache_keys_to_clear = []
            
            if exchange:
                # Clear cache for specific exchange
                cache_keys_to_clear.extend([
                    APIKeyManager._get_cache_key(f"user_{user.id}_exchange_{exchange}_creds"),
                    APIKeyManager._get_cache_key(f"user_{user.id}_validation_results"),
                ])
            else:
                # Clear all cache for user
                cache_keys_to_clear.extend([
                    APIKeyManager._get_cache_key(f"user_{user.id}_all_creds_all"),
                    APIKeyManager._get_cache_key(f"user_{user.id}_all_creds_validated"),
                    APIKeyManager._get_cache_key(f"user_{user.id}_validation_results"),
                ])
                # Also clear individual exchange caches
                user_exchanges = APIKey.objects.filter(user=user).values_list('exchange', flat=True)
                for user_exchange in user_exchanges:
                    cache_keys_to_clear.append(
                        APIKeyManager._get_cache_key(f"user_{user.id}_exchange_{user_exchange}_creds")
                    )
            
            # Clear the cache
            cache.delete_many(cache_keys_to_clear)
            
            logger.info(f"✅ Cleared credentials cache for {user.username}" + 
                       f" (exchange: {exchange})" if exchange else "")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear credentials cache: {e}")
            return False
    
    @staticmethod
    def get_usage_statistics(user: User) -> Dict[str, Any]:
        """
        Get usage statistics for user's API keys.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with usage statistics
        """
        stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'failed_retrievals': 0,
            'exchange_breakdown': {},
            'last_updated': timezone.now().isoformat()
        }
        
        try:
            # This would typically come from a usage tracking system
            # For now, we'll provide a basic implementation
            
            active_api_keys = APIKey.objects.filter(user=user, is_active=True)
            
            for api_key in active_api_keys:
                stats['exchange_breakdown'][api_key.exchange] = {
                    'is_validated': api_key.is_validated,
                    'last_used': api_key.last_used.isoformat() if api_key.last_used else 'Never',
                    'last_validated': api_key.last_validated.isoformat() if api_key.last_validated else 'Never',
                    'created_at': api_key.created_at.isoformat()
                }
            
            logger.debug(f"📊 Retrieved usage statistics for {user.username}")
            
        except Exception as e:
            logger.error(f"❌ Failed to get usage statistics: {e}")
            stats['error'] = str(e)
        
        return stats
    
    @staticmethod
    @transaction.atomic
    def bulk_validate_and_update(user: User) -> Dict[str, Any]:
        """
        Bulk validate and update all API keys for a user.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with bulk operation results
        """
        results = {
            'processed': 0,
            'updated': 0,
            'errors': [],
            'details': {}
        }
        
        try:
            active_api_keys = APIKey.objects.filter(user=user, is_active=True)
            
            for api_key in active_api_keys:
                try:
                    # Test connection
                    validation_result = APIKeyService.test_api_key_connection(api_key, force_test=True)
                    
                    # Update validation status
                    previous_status = api_key.is_validated
                    api_key.mark_as_validated(validation_result.get('connected', False))
                    
                    results['details'][api_key.exchange] = {
                        'previous_status': previous_status,
                        'current_status': api_key.is_validated,
                        'connected': validation_result.get('connected', False),
                        'error': validation_result.get('error')
                    }
                    
                    if previous_status != api_key.is_validated:
                        results['updated'] += 1
                    
                    results['processed'] += 1
                    
                except Exception as e:
                    results['errors'].append(f"{api_key.exchange}: {str(e)}")
                    results['details'][api_key.exchange] = {
                        'error': str(e),
                        'processed': False
                    }
            
            # Clear cache after bulk update
            APIKeyManager.rotate_credentials_cache(user)
            
            logger.info(f"✅ Bulk validation completed for {user.username}: "
                       f"{results['processed']} processed, {results['updated']} updated")
            
        except Exception as e:
            logger.error(f"❌ Bulk validation failed for {user.username}: {e}")
            results['errors'].append(f"Bulk operation failed: {str(e)}")
        
        return results