# backend/apps/users/services/security_service.py
import logging
from typing import Dict, Any, Tuple, Optional
from django.utils import timezone
from django.core.cache import cache
from ..models import APIKey, User
from ..utils.security import health_check, safe_decrypt_data, safe_encrypt_data, is_encrypted

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for security-related operations and API key validation"""
    
    @staticmethod
    def _validate_encryption_system() -> bool:
        """Validate that the encryption system is working properly"""
        try:
            health = health_check()
            if not health.get('ok', False):
                logger.error(f"Encryption system health check failed: {health}")
                return False
            return True
        except Exception as e:
            logger.error(f"Encryption system validation failed: {e}")
            return False
    
    @staticmethod
    def test_api_key_connection(api_key_instance: APIKey, force_test: bool = False) -> Dict[str, Any]:
        """
        Test API key connection to the exchange using CCXT.

        Args:
            api_key_instance: APIKey instance
            force_test: Whether to force test even if recently tested

        Returns:
            Dict with validation results
        """
        logger.info(f"🔍 Testing API key connection for {api_key_instance.exchange} (ID: {api_key_instance.id})")

        # Use recent cached validation (5 minutes) unless forced
        if not force_test and api_key_instance.last_validated:
            delta = timezone.now() - api_key_instance.last_validated
            if delta.total_seconds() < 300:  # 5 minutes
                logger.info(f"✅ Using cached validation for {api_key_instance.exchange} (ID: {api_key_instance.id})")
                return {
                    'api_key_id': api_key_instance.id,
                    'connected': bool(api_key_instance.is_validated),
                    'valid': bool(api_key_instance.is_validated),
                    'cached': True,
                    'exchange': api_key_instance.exchange,
                    'permissions': api_key_instance.permissions,
                    'message': 'Using cached validation',
                    'timestamp': timezone.now().isoformat()
                }

        # Default failure result template
        base_result = {
            'api_key_id': api_key_instance.id,
            'connected': False,
            'valid': False,
            'exchange': api_key_instance.exchange,
            'permissions': api_key_instance.permissions,
            'timestamp': timezone.now().isoformat(),
            'cached': False,
            'connector': None,
            'connector_info': {},
            'message': 'API key validation failed'
        }

        try:
            # Decrypt credentials
            try:
                credentials = api_key_instance.get_decrypted_keys()
                logger.info(f"✅ Successfully decrypted credentials for {api_key_instance.exchange} (ID: {api_key_instance.id})")
            except Exception as decryption_error:
                logger.error(f"❌ Failed to decrypt API key {api_key_instance.id}: {decryption_error}")
                base_result.update({
                    'message': f"Failed to decrypt API key: {str(decryption_error)}",
                    'error': str(decryption_error),
                })
                return base_result

            exchange_code = api_key_instance.exchange.lower()
            
            # Use CCXT for validation (matching your working implementation)
            try:
                import ccxt
                import os
                
                # Set environment variables temporarily for CCXT
                original_api_key = os.environ.get(f'{exchange_code.upper()}_API_KEY')
                original_secret = os.environ.get(f'{exchange_code.upper()}_SECRET_KEY')
                
                try:
                    # Set the credentials for this test
                    os.environ[f'{exchange_code.upper()}_API_KEY'] = credentials['api_key']
                    os.environ[f'{exchange_code.upper()}_SECRET_KEY'] = credentials['secret_key']
                    
                    # Create exchange instance based on exchange type
                    exchange_config = {
                        'apiKey': credentials['api_key'],
                        'secret': credentials['secret_key'],
                        'enableRateLimit': True,
                        'options': {
                            'adjustForTimeDifference': True,
                            'recvWindow': 60000,
                            'defaultType': 'spot',
                        }
                    }
                    
                    # Add passphrase for exchanges that require it
                    if exchange_code in ['okx', 'kucoin', 'coinbase'] and credentials.get('passphrase'):
                        exchange_config['password'] = credentials['passphrase']
                    
                    if exchange_code == 'binance':
                        exchange = ccxt.binance(exchange_config)
                    elif exchange_code == 'okx':
                        exchange = ccxt.okx(exchange_config)
                    elif exchange_code == 'kucoin':
                        exchange = ccxt.kucoin(exchange_config)
                    elif exchange_code == 'coinbase':
                        exchange = ccxt.coinbase(exchange_config)
                    elif exchange_code == 'kraken':
                        exchange = ccxt.kraken(exchange_config)
                    elif exchange_code == 'huobi':
                        exchange = ccxt.huobi(exchange_config)
                    elif exchange_code == 'bybit':
                        exchange = ccxt.bybit(exchange_config)
                    else:
                        msg = f"Unsupported exchange: {exchange_code}"
                        logger.warning(f"❌ {msg}")
                        base_result.update({'message': msg, 'error': msg})
                        return base_result
                    
                    # Test connection by fetching balance (this tests authentication)
                    logger.info(f"🔐 Testing {exchange_code} connection with balance fetch...")
                    
                    try:
                        # First load markets (public call)
                        exchange.load_markets()
                        logger.info(f"✅ Markets loaded for {exchange_code}")
                        
                        # Then try to fetch balance (authenticated call)
                        balance = exchange.fetch_balance()
                        
                        # Check if we got a valid balance response
                        if balance and 'total' in balance:
                            # Success - credentials are valid
                            total_balance = {k: v for k, v in balance['total'].items() if v > 0}
                            
                            result = {
                                'api_key_id': api_key_instance.id,
                                'connected': True,
                                'valid': True,
                                'exchange': exchange_code,
                                'timestamp': timezone.now().isoformat(),
                                'permissions': api_key_instance.permissions,
                                'connector': f'CCXT-{exchange.id}',
                                'connector_info': {
                                    'balance_currencies': len(total_balance),
                                    'has_trading_access': True,
                                },
                                'cached': False,
                                'message': f'API key validated successfully - Found {len(total_balance)} currencies with balance'
                            }
                            
                            logger.info(f"✅ API key validation successful for {exchange_code}")
                            return result
                        else:
                            # Balance fetch failed or returned empty
                            raise Exception("Balance fetch returned empty response")
                            
                    except ccxt.AuthenticationError as auth_error:
                        logger.error(f"❌ Authentication failed for {exchange_code}: {auth_error}")
                        base_result.update({
                            'message': f"Authentication failed: {str(auth_error)}",
                            'error': str(auth_error),
                            'connector_info': {'auth_error': True}
                        })
                        return base_result
                        
                    except ccxt.ExchangeError as exchange_error:
                        logger.error(f"❌ Exchange error for {exchange_code}: {exchange_error}")
                        base_result.update({
                            'message': f"Exchange error: {str(exchange_error)}",
                            'error': str(exchange_error)
                        })
                        return base_result
                        
                    except Exception as conn_error:
                        logger.error(f"❌ Connection test failed for {exchange_code}: {conn_error}")
                        base_result.update({
                            'message': f"Connection test failed: {str(conn_error)}",
                            'error': str(conn_error)
                        })
                        return base_result
                        
                finally:
                    # Restore original environment variables
                    if original_api_key:
                        os.environ[f'{exchange_code.upper()}_API_KEY'] = original_api_key
                    else:
                        os.environ.pop(f'{exchange_code.upper()}_API_KEY', None)
                        
                    if original_secret:
                        os.environ[f'{exchange_code.upper()}_SECRET_KEY'] = original_secret
                    else:
                        os.environ.pop(f'{exchange_code.upper()}_SECRET_KEY', None)
                        
            except ImportError:
                logger.error("❌ CCXT not available for API key validation")
                base_result.update({
                    'message': 'CCXT library not available for validation',
                    'error': 'CCXT not installed'
                })
                return base_result

        except Exception as e:
            logger.exception(f"❌ API key validation error for {api_key_instance.exchange} (APIKey ID: {api_key_instance.id}): {e}")
            base_result.update({'message': f"API key validation error: {str(e)}", 'error': str(e)})
            return base_result
    
    @staticmethod
    def validate_api_key_with_exchange(
        exchange: str, 
        api_key: str, 
        secret_key: str, 
        passphrase: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Comprehensive API key validation with exchange connectivity test using CCXT"""
        try:
            import ccxt
            
            exchange_config = {
                'apiKey': api_key,
                'secret': secret_key,
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000,
                }
            }
            
            # Add passphrase for supported exchanges
            if exchange.lower() in ['okx', 'kucoin', 'coinbase'] and passphrase:
                exchange_config['password'] = passphrase
            
            # Create exchange instance
            if exchange.lower() == 'binance':
                exchange_obj = ccxt.binance(exchange_config)
            elif exchange.lower() == 'okx':
                exchange_obj = ccxt.okx(exchange_config)
            elif exchange.lower() == 'kucoin':
                exchange_obj = ccxt.kucoin(exchange_config)
            else:
                return False, {'errors': [f'Unsupported exchange: {exchange}'], 'stage': 'exchange_setup'}
            
            try:
                # Test 1: Load markets (public endpoint)
                exchange_obj.load_markets()
                
                # Test 2: Fetch balance (authenticated endpoint)
                balance = exchange_obj.fetch_balance()
                
                # Test 3: Check if we have trading permissions by looking at balance structure
                has_trading_access = 'total' in balance and isinstance(balance['total'], dict)
                
                if has_trading_access:
                    return True, {
                        'message': 'API key validated successfully',
                        'details': {
                            'connected': True,
                            'permissions': ['read', 'trade'],  # Assuming both if balance works
                            'account_type': 'spot',
                            'balance_currencies': len([k for k, v in balance['total'].items() if v > 0])
                        }
                    }
                else:
                    return False, {
                        'errors': ['Could not verify trading permissions'],
                        'stage': 'permission_verification'
                    }
                    
            except ccxt.AuthenticationError as e:
                return False, {
                    'errors': [f'Authentication failed: {str(e)}'],
                    'stage': 'authentication'
                }
            except ccxt.ExchangeError as e:
                return False, {
                    'errors': [f'Exchange error: {str(e)}'],
                    'stage': 'exchange_connection'
                }
            except Exception as e:
                return False, {
                    'errors': [f'Validation error: {str(e)}'],
                    'stage': 'validation'
                }
                
        except ImportError:
            return False, {'errors': ['CCXT library not available'], 'stage': 'import'}
        except Exception as e:
            logger.exception("❌ Exchange validation error")
            return False, {
                'errors': [f'Exchange validation error: {str(e)}'],
                'stage': 'exchange_validation',
                'exception': str(e)
            }
    
    @staticmethod
    def rotate_encryption_for_user(user: User) -> Dict[str, Any]:
        """Re-encrypt all API keys for a user with new encryption key"""
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
                    # For each key, we need to decrypt with old key and encrypt with new key
                    # This requires both old and new keys to be available
                    
                    if api_key.is_encrypted:
                        try:
                            # Try to decrypt with current key
                            decrypted_values = api_key.get_decrypted_keys()
                            
                            # Store decrypted values temporarily
                            api_key.api_key = decrypted_values['api_key']
                            api_key.secret_key = decrypted_values['secret_key']
                            api_key.passphrase = decrypted_values.get('passphrase')
                            api_key.is_encrypted = False
                            
                            # Save without encryption first
                            api_key.save()
                            
                            # Now re-encrypt with new key
                            api_key.encrypt_keys(use_legacy_prefix=False)
                            api_key.save()
                            
                            results['successful'] += 1
                            logger.info(f"✅ Successfully rotated encryption for API key {api_key.id}")
                            
                        except Exception as decryption_error:
                            logger.error(f"❌ Failed to decrypt API key {api_key.id}: {decryption_error}")
                            results['failed'] += 1
                            results['errors'].append(f"Failed to decrypt key {api_key.id}: {str(decryption_error)}")
                    else:
                        # Key is not encrypted, just encrypt it with new key
                        api_key.encrypt_keys(use_legacy_prefix=False)
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
    
    @staticmethod
    def fix_encrypted_api_keys(user: User) -> Dict[str, Any]:
        """
        Fix API keys that have encryption issues by re-encrypting them.
        This should only be used when there are known encryption problems.
        """
        results = {
            'total_processed': 0,
            'fixed': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            api_keys = APIKey.objects.filter(user=user)
            
            for api_key in api_keys:
                try:
                    # If the key is marked as encrypted but can't be decrypted,
                    # we need to handle it specially
                    if api_key.is_encrypted:
                        try:
                            # Try to decrypt - if this fails, we have a problem
                            test_decrypt = api_key.get_decrypted_keys()
                            logger.info(f"✅ API key {api_key.id} decrypts successfully")
                            results['fixed'] += 0  # Not actually fixed, just verified
                            
                        except Exception as decrypt_error:
                            logger.warning(f"⚠️ API key {api_key.id} has decryption issues: {decrypt_error}")
                            
                            # If we can't decrypt, we need to mark it as needing re-entry
                            api_key.is_validated = False
                            api_key.validation_message = "Encryption key mismatch - please re-enter API credentials"
                            api_key.save()
                            
                            results['fixed'] += 1
                            results['errors'].append(f"API key {api_key.id} has encryption issues and was marked for re-entry")
                    
                    results['total_processed'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to process key {api_key.id}: {str(e)}")
            
            logger.info(f"✅ Encryption fix completed: {results['fixed']} fixed, {results['failed']} failed")
            
        except Exception as e:
            logger.error(f"❌ Encryption fix failed: {e}")
            results['errors'].append(f"Fix process failed: {str(e)}")
        
        return results