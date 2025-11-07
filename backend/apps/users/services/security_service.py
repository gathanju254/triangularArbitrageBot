# backend/apps/users/services/security_service.py
import logging
from typing import Dict, Any, Tuple
from django.utils import timezone
from django.core.cache import cache
from ..models import APIKey, User
from utils.security import health_check

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for security-related operations and API key validation"""
    
    @staticmethod
    def _validate_encryption_system() -> bool:
        """Validate that the encryption system is working properly"""
        try:
            health = health_check()
            if not health['healthy']:
                logger.error(f"Encryption system health check failed: {health['errors']}")
                return False
            return True
        except Exception as e:
            logger.error(f"Encryption system validation failed: {e}")
            return False
    
    @staticmethod
    def test_api_key_connection(api_key_instance: APIKey, force_test: bool = False) -> Dict[str, Any]:
        """Test API key connectivity with the exchange"""
        # Check if we recently tested this key
        if not force_test and api_key_instance.last_validated:
            time_since_validation = timezone.now() - api_key_instance.last_validated
            if time_since_validation.total_seconds() < 300:  # 5 minutes
                return {
                    'connected': api_key_instance.is_validated,
                    'cached': True,
                    'exchange': api_key_instance.exchange,
                    'last_validated': api_key_instance.last_validated.isoformat()
                }
        
        try:
            # Get decrypted keys for testing
            decrypted_keys = api_key_instance.get_decrypted_keys()
            
            # Import exchange service
            from apps.exchanges.services import ExchangeService
            
            # Test connection
            exchange_service = ExchangeService()
            result = exchange_service.test_connection(
                exchange=api_key_instance.exchange,
                api_key=decrypted_keys['api_key'],
                secret_key=decrypted_keys['secret_key'],
                passphrase=decrypted_keys.get('passphrase')
            )
            
            # Update usage and validation status
            api_key_instance.last_used = timezone.now()
            if result.get('connected', False):
                api_key_instance.mark_as_validated(True)
                logger.info(f"✅ API key {api_key_instance.id} validated for {api_key_instance.exchange}")
            else:
                api_key_instance.mark_as_validated(False)
                logger.warning(f"❌ API key {api_key_instance.id} validation failed")
            
            return {
                'connected': result.get('connected', False),
                'exchange': api_key_instance.exchange,
                'api_key_id': api_key_instance.id,
                'permissions': result.get('permissions', []),
                'account_type': result.get('account_type', 'unknown'),
                'error': result.get('error'),
                'timestamp': timezone.now().isoformat()
            }
            
        except ImportError:
            logger.error("Exchange service not available for API key testing")
            return {
                'connected': False,
                'error': 'Exchange service not available',
                'exchange': api_key_instance.exchange,
                'api_key_id': api_key_instance.id
            }
        except Exception as e:
            logger.error(f"❌ API key test failed: {e}")
            return {
                'connected': False,
                'error': str(e),
                'exchange': api_key_instance.exchange,
                'api_key_id': api_key_instance.id
            }
    
    @staticmethod
    def validate_api_key_with_exchange(
        exchange: str, 
        api_key: str, 
        secret_key: str, 
        passphrase: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Comprehensive API key validation with exchange connectivity test"""
        try:
            from apps.exchanges.services import ExchangeService
        except Exception as e:
            return False, {'errors': ['Exchange service not available'], 'stage': 'import'}

        # Step 1: Basic format validation
        from .api_key_service import APIKeyService
        is_valid, errors = APIKeyService.validate_api_key_data(exchange, api_key, secret_key, passphrase)
        if not is_valid:
            return False, {'errors': errors, 'stage': 'format_validation'}

        # Step 2: Exchange connectivity test
        try:
            exchange_service = ExchangeService()
            validation_result = exchange_service.test_api_key_connection(
                exchange=exchange,
                api_key=api_key,
                secret_key=secret_key,
                passphrase=passphrase
            )

            if not validation_result.get('connected', False):
                return False, {
                    'errors': [validation_result.get('error', 'Connection failed')],
                    'stage': 'exchange_connection',
                    'details': validation_result
                }

            # Step 3: Check trading permissions
            permissions = validation_result.get('permissions', []) or validation_result.get('scopes', [])
            if not any(p in permissions for p in ('trade', 'spot_trade', 'orders', 'trade:write')):
                return False, {
                    'errors': ['API key does not have trading permissions'],
                    'stage': 'permission_check',
                    'details': validation_result
                }

            return True, {
                'message': 'API key validated successfully',
                'details': validation_result
            }

        except Exception as e:
            logger.exception("❌ Exchange validation error")
            return False, {
                'errors': [f'Exchange validation error: {str(e)}'],
                'stage': 'exchange_validation',
                'exception': str(e)
            }
    
    @staticmethod
    def rotate_encryption_for_user(user: User) -> Dict[str, Any]:
        """Re-encrypt all API keys for a user"""
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            api_keys = APIKey.objects.filter(user=user)
            
            for api_key in api_keys:
                try:
                    if api_key.is_encrypted:
                        # Decrypt first to get original values
                        decrypted_values = api_key.get_decrypted_keys()
                        
                        # Update with decrypted values and mark for re-encryption
                        api_key.api_key = decrypted_values['api_key']
                        api_key.secret_key = decrypted_values['secret_key']
                        api_key.passphrase = decrypted_values.get('passphrase')
                        api_key.is_encrypted = False
                        
                        api_key.save()
                    
                    results['successful'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to rotate key {api_key.id}: {str(e)}")
                
                results['total_processed'] += 1
            
            # Clear all user-related caches
            from .api_key_service import APIKeyService
            cache_keys = [
                APIKeyService._get_cache_key(f"user_{user.id}_active"),
                APIKeyService._get_cache_key(f"user_{user.id}_all"),
                APIKeyService._get_cache_key(f"user_{user.id}_stats"),
            ]
            for api_key in api_keys:
                cache_keys.append(APIKeyService._get_cache_key(f"apikey_{api_key.id}_decrypted"))
            
            cache.delete_many(cache_keys)
            
            logger.info(f"✅ Encryption rotation completed: {results['successful']} successful, {results['failed']} failed")
            
        except Exception as e:
            logger.error(f"❌ Encryption rotation failed: {e}")
            results['errors'].append(f"Rotation process failed: {str(e)}")
        
        return results