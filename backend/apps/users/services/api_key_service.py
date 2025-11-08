# backend/apps/users/services/api_key_service.py
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.cache import cache
from ..models import APIKey, User

logger = logging.getLogger(__name__)


class APIKeyService:
    """Core service for API key management operations"""
    
    EXCHANGE_REQUIREMENTS = {
        'binance': {
            'min_api_key_len': 64,
            'min_secret_len': 64,
            'requires_passphrase': False,
            'api_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$',
            'secret_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$'
        },
        'coinbase': {
            'min_api_key_len': 36,
            'min_secret_len': 50,
            'requires_passphrase': False,
            'api_key_pattern': r'^organizations/[a-f0-9\-]+/apiKeys/[a-f0-9\-]+$',
            'secret_key_pattern': r'^[\s\S]*$'
        },
        'kraken': {
            'min_api_key_len': 36,
            'min_secret_len': 64,
            'requires_passphrase': False,
            'api_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$',
            'secret_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$'
        },
        'kucoin': {
            'min_api_key_len': 24,
            'min_secret_len': 36,
            'requires_passphrase': True,
            'api_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$',
            'secret_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$'
        },
        'okx': {
            'min_api_key_len': 36,
            'min_secret_len': 42,
            'requires_passphrase': True,
            'api_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$',
            'secret_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$'
        },
        'huobi': {
            'min_api_key_len': 24,
            'min_secret_len': 32,
            'requires_passphrase': False,
            'api_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$',
            'secret_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$'
        },
        'bybit': {
            'min_api_key_len': 36,
            'min_secret_len': 32,
            'requires_passphrase': False,
            'api_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$',
            'secret_key_pattern': r'^[A-Za-z0-9\-_.:=+/]+$'
        },
    }
    
    CACHE_TIMEOUT = 300
    CACHE_PREFIX = "apikey_service"
    
    @staticmethod
    def _get_cache_key(key_suffix: str) -> str:
        return f"{APIKeyService.CACHE_PREFIX}:{key_suffix}"
    
    @staticmethod
    def validate_api_key_data(exchange: str, api_key: str, secret_key: str, passphrase: str = None) -> Tuple[bool, List[str]]:
        """Validate API key data format and requirements"""
        errors = []
        
        if not api_key or not secret_key:
            errors.append("API key and secret key are required")
            return False, errors
        
        exchange_lower = exchange.lower()
        requirements = APIKeyService.EXCHANGE_REQUIREMENTS.get(exchange_lower, {
            'min_api_key_len': 20,
            'min_secret_len': 20,
            'requires_passphrase': False
        })
        
        # Length validation
        if len(api_key.strip()) < requirements.get('min_api_key_len', 20):
            errors.append(f"API key too short for {exchange}. Minimum: {requirements['min_api_key_len']}")
        
        if len(secret_key.strip()) < requirements.get('min_secret_len', 20):
            errors.append(f"Secret key too short for {exchange}. Minimum: {requirements['min_secret_len']}")
        
        # Passphrase validation
        if requirements.get('requires_passphrase', False) and not passphrase:
            errors.append(f"{exchange} requires a passphrase")
        
        # Special handling for Coinbase
        if exchange_lower == 'coinbase':
            is_uuid_format = re.match(r'^[A-Za-z0-9\-_]+$', api_key.strip())
            is_advanced_trade_format = re.match(r'^organizations/[a-f0-9\-]+/apiKeys/[a-f0-9\-]+$', api_key.strip())
            
            if not (is_uuid_format or is_advanced_trade_format):
                errors.append("Coinbase API key should be UUID or Advanced Trade format")
                
            if not secret_key.strip().startswith('-----BEGIN'):
                errors.append("Coinbase secret key should be PEM format")
                
        else:
            # Standard validation
            api_pattern = requirements.get('api_key_pattern', r'^[A-Za-z0-9\-_.]+$')
            secret_pattern = requirements.get('secret_key_pattern', r'^[A-Za-z0-9\-_.+/=]+$')

            try:
                if not re.match(api_pattern, api_key.strip()):
                    errors.append(f"API key contains invalid characters for {exchange}")
            except re.error:
                if not all(c.isalnum() or c in '-_.' for c in api_key.strip()):
                    errors.append("API key contains invalid characters")

            try:
                if not re.match(secret_pattern, secret_key.strip()):
                    errors.append(f"Secret key contains invalid characters for {exchange}")
            except re.error:
                if not all(c.isalnum() or c in '-_+/=' for c in secret_key.strip()):
                    errors.append("Secret key contains invalid characters")
        
        return len(errors) == 0, errors
    
    @staticmethod
    @transaction.atomic
    def create_api_key(
        user: User, 
        exchange: str, 
        api_key: str, 
        secret_key: str, 
        passphrase: str = None, 
        label: str = None,
        auto_validate: bool = False,
        permissions: List[str] = None
    ) -> APIKey:
        """Create a new API key with automatic encryption"""
        logger.info(f"🔑 Creating API key for {user.username} on {exchange}")
        
        # Validate input data
        is_valid, errors = APIKeyService.validate_api_key_data(exchange, api_key, secret_key, passphrase)
        if not is_valid:
            raise ValueError(f"Invalid API key data: {', '.join(errors)}")
        
        # Check for existing API key
        existing_key = APIKey.objects.filter(user=user, exchange=exchange).first()
        if existing_key:
            raise ValueError(f"API key for {exchange} already exists")
        
        try:
            # Set default permissions if not provided
            if permissions is None:
                permissions = ['read', 'trade']  # Default to read and trade permissions
            
            # Create API key instance
            api_key_instance = APIKey(
                user=user,
                exchange=exchange,
                label=label,
                api_key=api_key.strip(),
                secret_key=secret_key.strip(),
                passphrase=passphrase.strip() if passphrase else None,
                permissions=permissions,
                is_encrypted=False,
                is_validated=False
            )
            
            api_key_instance.full_clean()
            api_key_instance.save()
            
            logger.info(f"✅ API key created successfully for {exchange} (ID: {api_key_instance.id})")
            
            # Auto-validate if requested
            if auto_validate:
                try:
                    from .security_service import SecurityService
                    validation_result = SecurityService.test_api_key_connection(api_key_instance)
                    if validation_result.get('connected', False):
                        api_key_instance.mark_as_validated(True)
                        logger.info(f"✅ API key auto-validated for {exchange}")
                except Exception as validation_error:
                    logger.warning(f"⚠️ Auto-validation error: {validation_error}")
            
            # Clear caches
            cache_keys = [
                APIKeyService._get_cache_key(f"user_{user.id}_active"),
                APIKeyService._get_cache_key(f"user_{user.id}_all"),
                APIKeyService._get_cache_key(f"user_{user.id}_trading"),
            ]
            cache.delete_many(cache_keys)
            
            return api_key_instance
            
        except Exception as e:
            logger.error(f"❌ Failed to create API key: {e}")
            raise ValueError(f"Failed to create API key: {str(e)}") from e
    
    @staticmethod
    def get_api_keys(user: User, active_only: bool = False, use_cache: bool = True) -> List[APIKey]:
        """Get user's API keys with optional caching"""
        cache_key = APIKeyService._get_cache_key(f"user_{user.id}_{'active' if active_only else 'all'}")
        
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        try:
            queryset = APIKey.objects.filter(user=user)
            if active_only:
                queryset = queryset.filter(is_active=True)
            
            api_keys = list(queryset.order_by('-created_at'))
            
            if use_cache:
                cache.set(cache_key, api_keys, APIKeyService.CACHE_TIMEOUT)
            
            return api_keys
            
        except Exception as e:
            logger.error(f"❌ Failed to get API keys: {e}")
            return []
    
    @staticmethod
    def get_api_key_with_decrypted_values(api_key_id: int, user: User, use_cache: bool = True) -> Dict[str, Any]:
        """Get API key with decrypted values for trading operations"""
        cache_key = APIKeyService._get_cache_key(f"apikey_{api_key_id}_decrypted")
        
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        try:
            api_key = APIKey.objects.get(id=api_key_id, user=user)
            
            if not api_key.is_active:
                raise ValueError("API key is not active")
            
            decrypted_values = api_key.get_decrypted_keys()
            
            result = {
                'id': api_key.id,
                'exchange': api_key.exchange,
                'label': api_key.label,
                'is_active': api_key.is_active,
                'is_validated': api_key.is_validated,
                'is_encrypted': api_key.is_encrypted,
                'permissions': api_key.permissions,
                'requests_per_minute': api_key.requests_per_minute,
                'last_request_time': api_key.last_request_time.isoformat() if api_key.last_request_time else None,
                'created_at': api_key.created_at.isoformat() if api_key.created_at else None,
                'last_used': api_key.last_used.isoformat() if api_key.last_used else None,
                'last_validated': api_key.last_validated.isoformat() if api_key.last_validated else None,
                'requires_passphrase': api_key.requires_passphrase,
                **decrypted_values
            }
            
            if use_cache:
                cache.set(cache_key, result, 60)  # 1 minute for sensitive data
            
            return result
            
        except APIKey.DoesNotExist:
            raise ValueError("API key not found or access denied")
        except Exception as e:
            logger.error(f"❌ Failed to get decrypted values: {e}")
            raise ValueError(f"Failed to decrypt API key: {str(e)}") from e
    
    @staticmethod
    def get_user_api_key_stats(user: User) -> Dict[str, Any]:
        """Get statistics about user's API keys"""
        cache_key = APIKeyService._get_cache_key(f"user_{user.id}_stats")
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        try:
            all_keys = APIKey.objects.filter(user=user)
            active_keys = all_keys.filter(is_active=True)
            validated_keys = active_keys.filter(is_validated=True)
            
            # Fix: Replace contains lookup with manual filtering for trading keys
            trading_keys = 0
            for key in active_keys.filter(is_validated=True):
                if 'trade' in key.permissions:
                    trading_keys += 1
            
            # Permission statistics
            read_keys = active_keys.filter(permissions__ilike='%read%')
            trade_keys = active_keys.filter(permissions__ilike='%trade%')
            withdraw_keys = active_keys.filter(permissions__ilike='%withdraw%')
            
            stats = {
                'total_keys': all_keys.count(),
                'active_keys': active_keys.count(),
                'validated_keys': validated_keys.count(),
                'trading_keys': trading_keys,
                'validation_rate': round((validated_keys.count() / active_keys.count() * 100) if active_keys.count() > 0 else 0, 1),
                'exchanges': list(all_keys.values_list('exchange', flat=True).distinct()),
                'recently_used': all_keys.filter(last_used__isnull=False).order_by('-last_used')[:5].count(),
                'last_created': all_keys.order_by('-created_at').first().created_at.isoformat() if all_keys.exists() else None,
                'permission_stats': {
                    'read': read_keys.count(),
                    'trade': trade_keys.count(),
                    'withdraw': withdraw_keys.count(),
                }
            }
            
            cache.set(cache_key, stats, APIKeyService.CACHE_TIMEOUT)
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get API key stats: {e}")
            return {
                'total_keys': 0,
                'active_keys': 0,
                'validated_keys': 0,
                'trading_keys': 0,
                'validation_rate': 0,
                'exchanges': [],
                'recently_used': 0,
                'last_created': None,
                'permission_stats': {
                    'read': 0,
                    'trade': 0,
                    'withdraw': 0,
                }
            }
    
    @staticmethod
    def get_user_api_key_stats_simple(user: User) -> Dict[str, Any]:
        """Get simplified API key statistics for a user"""
        try:
            api_keys = APIKey.objects.filter(user=user)
            total = api_keys.count()
            active = api_keys.filter(is_active=True).count()
            validated = api_keys.filter(is_active=True, is_validated=True).count()
            
            # Fix: Replace contains lookup with manual filtering
            trading_keys = 0
            for key in api_keys.filter(is_active=True, is_validated=True):
                if 'trade' in key.permissions:
                    trading_keys += 1
            
            # Get exchanges with active keys
            exchanges_with_keys = api_keys.filter(is_active=True).values_list('exchange', flat=True).distinct().count()
            
            return {
                'total_keys': total,
                'active_keys': active,
                'validated_keys': validated,
                'trading_keys': trading_keys,
                'exchanges_with_keys': exchanges_with_keys,
                'validation_rate': round((validated / active * 100) if active > 0 else 0, 1),
                'health_status': 'healthy' if validated > 0 else 'needs_attention'
            }
            
        except Exception as e:
            logger.error(f"Failed to get API key stats: {e}")
            return {
                'total_keys': 0,
                'active_keys': 0,
                'validated_keys': 0,
                'trading_keys': 0,
                'exchanges_with_keys': 0,
                'validation_rate': 0,
                'health_status': 'error'
            }
    
    @staticmethod
    def get_user_exchange_connector(user, exchange: str):
        """
        Get exchange connector for user's API key with enhanced security.
        
        Args:
            user: User object
            exchange: Exchange name
            
        Returns:
            Exchange connector instance
        """
        try:
            # Get active, validated API key for the exchange
            api_key = APIKey.objects.get(
                user=user, 
                exchange=exchange, 
                is_active=True, 
                is_validated=True
            )
            
            # Check if API key has trading permissions
            if not api_key.has_permission('trade'):
                raise ValueError(f"API key for {exchange} does not have trading permissions")
            
            # Check rate limits
            if not api_key.check_rate_limit():
                raise ValueError(f"Rate limit exceeded for {exchange}")
            
            # Get decrypted credentials
            credentials = api_key.get_decrypted_keys()
            
            # Import exchange connector
            from apps.exchanges.connectors.base import BaseExchangeConnector
            connector_class = BaseExchangeConnector.get_connector(exchange)
            
            # Create connector instance
            connector = connector_class(
                api_key=credentials['api_key'],
                secret_key=credentials['secret_key'],
                passphrase=credentials.get('passphrase')
            )
            
            # Mark as used for rate limiting
            api_key.record_usage()
            
            logger.info(f"✅ Created exchange connector for {exchange} (user: {user.username})")
            return connector
            
        except APIKey.DoesNotExist:
            logger.error(f"❌ No active API key found for {exchange} (user: {user.username})")
            raise ValueError(f"No active API key found for {exchange}")
        except Exception as e:
            logger.error(f"❌ Failed to create connector for {exchange}: {e}")
            raise
    
    @staticmethod
    def validate_api_key_permissions(api_key_instance: APIKey, required_permission: str) -> bool:
        """
        Validate that API key has required permissions.
        
        Args:
            api_key_instance: APIKey instance
            required_permission: Required permission ('read', 'trade', 'withdraw')
            
        Returns:
            True if permission is granted
        """
        return api_key_instance.has_permission(required_permission)
    
    @staticmethod
    def get_trading_api_keys(user) -> List[APIKey]:
        """
        Get all API keys with trading permissions.
        
        Args:
            user: User object
            
        Returns:
            List of APIKey instances with trading permissions
        """
        cache_key = APIKeyService._get_cache_key(f"user_{user.id}_trading")
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        try:
            trading_keys = APIKey.get_trading_keys_for_user(user)
            
            if trading_keys:
                cache.set(cache_key, list(trading_keys), APIKeyService.CACHE_TIMEOUT)
            
            return list(trading_keys)
            
        except Exception as e:
            logger.error(f"❌ Failed to get trading API keys: {e}")
            return []
    
    @staticmethod
    def update_api_key_permissions(api_key_id: int, user: User, permissions: List[str]) -> APIKey:
        """
        Update API key permissions.
        
        Args:
            api_key_id: ID of the API key to update
            user: User owning the API key
            permissions: New list of permissions
            
        Returns:
            Updated APIKey instance
        """
        try:
            api_key = APIKey.objects.get(id=api_key_id, user=user)
            
            # Validate permissions
            valid_permissions = [p[0] for p in APIKey.PERMISSION_SCOPES]
            for perm in permissions:
                if perm not in valid_permissions:
                    raise ValueError(f"Invalid permission: {perm}. Must be one of: {valid_permissions}")
            
            api_key.permissions = permissions
            api_key.full_clean()
            api_key.save()
            
            # Clear relevant caches
            cache_keys = [
                APIKeyService._get_cache_key(f"user_{user.id}_active"),
                APIKeyService._get_cache_key(f"user_{user.id}_all"),
                APIKeyService._get_cache_key(f"user_{user.id}_trading"),
                APIKeyService._get_cache_key(f"apikey_{api_key_id}_decrypted"),
            ]
            cache.delete_many(cache_keys)
            
            logger.info(f"✅ Updated permissions for API key {api_key_id}: {permissions}")
            return api_key
            
        except APIKey.DoesNotExist:
            raise ValueError("API key not found or access denied")
        except Exception as e:
            logger.error(f"❌ Failed to update API key permissions: {e}")
            raise ValueError(f"Failed to update permissions: {str(e)}") from e
    
    @staticmethod
    def check_rate_limit_status(api_key_instance: APIKey) -> Dict[str, Any]:
        """
        Check rate limit status for an API key.
        
        Args:
            api_key_instance: APIKey instance
            
        Returns:
            Dictionary with rate limit information
        """
        try:
            is_within_limit = api_key_instance.check_rate_limit()
            time_since_last_request = None
            
            if api_key_instance.last_request_time:
                time_since_last_request = (timezone.now() - api_key_instance.last_request_time).total_seconds()
            
            return {
                'is_within_limit': is_within_limit,
                'requests_per_minute': api_key_instance.requests_per_minute,
                'last_request_time': api_key_instance.last_request_time.isoformat() if api_key_instance.last_request_time else None,
                'time_since_last_request': time_since_last_request,
                'min_time_between_requests': 60.0 / api_key_instance.requests_per_minute,
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to check rate limit status: {e}")
            return {
                'is_within_limit': False,
                'requests_per_minute': api_key_instance.requests_per_minute,
                'last_request_time': None,
                'time_since_last_request': None,
                'min_time_between_requests': 60.0 / api_key_instance.requests_per_minute,
            }
    
    @staticmethod
    def get_api_key_usage_stats(api_key_instance: APIKey, days: int = 7) -> Dict[str, Any]:
        """
        Get usage statistics for an API key.
        
        Args:
            api_key_instance: APIKey instance
            days: Number of days to look back
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            from ..models import APIKeyUsageLog
            return APIKeyUsageLog.get_usage_statistics(api_key_instance, days)
        except Exception as e:
            logger.error(f"❌ Failed to get API key usage stats: {e}")
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'success_rate': 0,
            }
    
    @staticmethod
    def bulk_update_api_keys(user: User, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform bulk updates on multiple API keys.
        
        Args:
            user: User owning the API keys
            updates: List of update operations
            
        Returns:
            Dictionary with operation results
        """
        results = {
            'successful': 0,
            'failed': 0,
            'errors': [],
            'details': []
        }
        
        for update in updates:
            try:
                api_key_id = update.get('api_key_id')
                operation = update.get('operation')
                data = update.get('data', {})
                
                if operation == 'update_permissions':
                    api_key = APIKeyService.update_api_key_permissions(api_key_id, user, data.get('permissions', []))
                    results['details'].append({
                        'operation': 'update_permissions',
                        'api_key_id': api_key_id,
                        'status': 'success',
                        'message': f'Updated permissions for API key {api_key_id}'
                    })
                    results['successful'] += 1
                    
                elif operation == 'toggle_active':
                    api_key = APIKey.objects.get(id=api_key_id, user=user)
                    new_active_state = not api_key.is_active
                    api_key.is_active = new_active_state
                    api_key.save()
                    
                    results['details'].append({
                        'operation': 'toggle_active',
                        'api_key_id': api_key_id,
                        'status': 'success',
                        'message': f'Set active to {new_active_state} for API key {api_key_id}'
                    })
                    results['successful'] += 1
                    
                elif operation == 'update_rate_limit':
                    api_key = APIKey.objects.get(id=api_key_id, user=user)
                    new_rate_limit = data.get('requests_per_minute', 60)
                    api_key.requests_per_minute = new_rate_limit
                    api_key.save()
                    
                    results['details'].append({
                        'operation': 'update_rate_limit',
                        'api_key_id': api_key_id,
                        'status': 'success',
                        'message': f'Updated rate limit to {new_rate_limit} for API key {api_key_id}'
                    })
                    results['successful'] += 1
                    
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Unknown operation: {operation}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Operation failed for API key {update.get('api_key_id')}: {str(e)}")
                results['details'].append({
                    'operation': update.get('operation', 'unknown'),
                    'api_key_id': update.get('api_key_id'),
                    'status': 'error',
                    'message': str(e)
                })
        
        # Clear all user-related caches
        cache_keys = [
            APIKeyService._get_cache_key(f"user_{user.id}_active"),
            APIKeyService._get_cache_key(f"user_{user.id}_all"),
            APIKeyService._get_cache_key(f"user_{user.id}_trading"),
            APIKeyService._get_cache_key(f"user_{user.id}_stats"),
        ]
        cache.delete_many(cache_keys)
        
        logger.info(f"✅ Bulk operations completed: {results['successful']} successful, {results['failed']} failed")
        return results