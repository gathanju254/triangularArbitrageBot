# backend/apps/users/signals.py

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.conf import settings
from .models import User, UserProfile, APIKey
from .tasks import send_welcome_email

# Get logger instance
logger = logging.getLogger(__name__)


def send_welcome_email_robust(user_id):
    """Robust welcome email sender with fallback mechanisms"""
    # Try async first with Celery
    from celery import current_app
    try:
        # Check if Celery workers are active
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
    except Exception as e:
        logger.warning(f"⚠️ Error checking Celery workers: {e}")
        active_workers = None
        
        if active_workers:
            send_welcome_email.delay(user_id)
            logger.info("✅ Welcome email queued via Celery")
            return
        else:
            logger.warning("⚠️ No active Celery workers found")
    except Exception as e:
        logger.warning(f"⚠️ Celery unavailable: {e}")
    
    # Fallback to synchronous sending
    try:
        result = send_welcome_email(user_id)
        logger.info("✅ Welcome email sent synchronously")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email: {e}")
        return f"Failed to send welcome email: {str(e)}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when a new user is created"""
    if created:
        logger.info(f"👤 Creating user profile for {instance.username}")
        
        try:
            # Create user profile
            UserProfile.objects.create(user=instance)
            logger.info(f"✅ User profile created for {instance.username}")
        except Exception as e:
            logger.error(f"❌ Failed to create user profile for {instance.username}: {e}")
            # Don't raise exception to avoid breaking user creation
            return

        # Add to default group
        try:
            default_group, created = Group.objects.get_or_create(name='Traders')
            instance.groups.add(default_group)
            if created:
                logger.info(f"✅ Created 'Traders' group and added {instance.username}")
            else:
                logger.info(f"✅ Added {instance.username} to 'Traders' group")
        except Exception as e:
            logger.error(f"❌ Failed to add {instance.username} to Traders group: {e}")
            # Continue with email sending even if group assignment fails

        # Enhanced Redis health check before sending welcome email
        logger.info(f"📧 Preparing to send welcome email for {instance.username}")
        
        redis_available = False
        celery_available = False
        
        # Check Redis availability with timeout
        try:
            from django.core.cache import cache
            import redis
            
            # Test Redis connection with short timeout
            redis_url = getattr(settings, 'REDIS_URL', None)
            if redis_url:
                r = redis.from_url(redis_url, socket_connect_timeout=2)
                r.ping()
                redis_available = True
                logger.info("✅ Redis connection confirmed - available for Celery")
            else:
                logger.warning("⚠️ No Redis URL configured in settings")
                redis_available = False
                
        except (redis.ConnectionError, AttributeError, ValueError) as e:
            logger.warning(f"⚠️ Redis connection unavailable: {e}")
            redis_available = False
        except Exception as e:
            logger.warning(f"⚠️ Redis connection test failed: {e}")
            redis_available = False

        # If Redis is available, test Celery broker connection
        if redis_available:
            try:
                # Quick test to see if Celery can queue tasks
                test_result = send_welcome_email.apply_async(
                    args=[instance.id], 
                    queue='users',
                    expires=300,  # 5 minute expiration
                    retry=False  # Don't retry the test
                )
                celery_available = True
                logger.info(f"✅ Celery broker confirmed - task queued with ID: {test_result.id}")
            except Exception as e:
                logger.warning(f"⚠️ Celery broker test failed: {e}")
                celery_available = False
        else:
            celery_available = False

        # Decision logic for email sending method
        if redis_available and celery_available:
            # Both Redis and Celery are available - use async
            try:
                send_welcome_email.delay(instance.id)
                logger.info(f"✅ Welcome email queued via Celery for {instance.username}")
            except Exception as e:
                logger.warning(f"⚠️ Celery queue failed, falling back to sync: {e}")
                send_welcome_email_sync(instance)
        else:
            # Redis or Celery unavailable - use synchronous sending
            if not redis_available:
                logger.warning("⚠️ Redis unavailable - sending welcome email synchronously")
            elif not celery_available:
                logger.warning("⚠️ Celery broker unavailable - sending welcome email synchronously")
            else:
                logger.warning("⚠️ Both Redis and Celery unavailable - sending welcome email synchronously")
            send_welcome_email_sync(instance)


def send_welcome_email_sync(user_instance):
    """Helper function to send welcome email synchronously with error handling"""
    try:
        logger.info(f"🔄 Sending welcome email synchronously for {user_instance.username}")
        # Call the task function directly (bypassing Celery)
        result = send_welcome_email(user_instance.id)
        logger.info(f"✅ Synchronous welcome email completed: {result}")
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email synchronously for {user_instance.username}: {e}")
        # Don't raise exception - user creation should still succeed even if email fails


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'profile'):
        try:
            instance.profile.save()
            logger.debug(f"💾 User profile saved for {instance.username}")
        except Exception as e:
            logger.error(f"❌ Failed to save user profile for {instance.username}: {e}")


@receiver(post_save, sender=APIKey)
def encrypt_api_key(sender, instance, created, **kwargs):
    """Encrypt API keys before saving"""
    if created and not instance.is_encrypted:
        logger.info(f"🔐 Encrypting new API key for {instance.exchange} (User: {instance.user.username})")
        try:
            instance.encrypt_keys()
            logger.info(f"✅ API key encrypted successfully for {instance.exchange}")
        except Exception as e:
            logger.error(f"❌ Failed to encrypt API key for {instance.exchange}: {e}")
            # Don't raise exception to avoid breaking API key creation
    elif not created and not instance.is_encrypted:
        # Handle case where API key was created without encryption and is being updated
        logger.info(f"🔐 Encrypting existing API key for {instance.exchange} (User: {instance.user.username})")
        try:
            instance.encrypt_keys()
            logger.info(f"✅ Existing API key encrypted successfully for {instance.exchange}")
        except Exception as e:
            logger.error(f"❌ Failed to encrypt existing API key for {instance.exchange}: {e}")


@receiver(post_save, sender=APIKey)
def log_api_key_activity(sender, instance, created, **kwargs):
    """Log API key creation and updates for audit purposes"""
    if created:
        logger.info(f"🔑 New API key created: {instance.exchange} for {instance.user.username} (ID: {instance.id})")
    else:
        logger.info(f"🔧 API key updated: {instance.exchange} for {instance.user.username} (ID: {instance.id})")
        
        # Log specific field changes if needed
        update_fields = kwargs.get('update_fields')
        if update_fields:
            logger.debug(f"📝 API key update fields: {list(update_fields)}")


@receiver(post_save, sender=UserProfile)
def log_user_profile_changes(sender, instance, created, **kwargs):
    """Log user profile changes for audit purposes"""
    if created:
        logger.info(f"👤 User profile created for {instance.user.username}")
    else:
        logger.debug(f"🔧 User profile updated for {instance.user.username}")
        
        # Log risk tolerance changes specifically
        update_fields = kwargs.get('update_fields')
        if update_fields and 'risk_tolerance' in update_fields:
            logger.info(f"🎯 Risk tolerance updated for {instance.user.username}: {instance.risk_tolerance}")


def ready():
    """Signal handler registration - can be used for additional setup"""
    logger.info("✅ User signals registered successfully")
    # Additional signal registration can go here if needed