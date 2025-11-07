# backend/apps/users/tasks.py

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import User
from .models import APIKey
from apps.exchanges.services import ExchangeService

# Get logger instance
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """Send welcome email to new user with retry capability"""
    try:
        user = User.objects.get(id=user_id)
        
        # Log email attempt
        logger.info(f"📧 Attempting to send welcome email to {user.email}")

        subject = "Welcome to Tudollar!"
        message = f"""
Hello {user.username},

Welcome to Tudollar - Your automated arbitrage trading platform!

You can now:
✅ Add your API keys
✅ Set risk and trade settings
✅ Start real-time arbitrage monitoring

Need help? Reply to this email.

Happy trading!
Tudollar Team
"""

        # Log before sending
        logger.info(f"📧 Sending email to {user.email} with subject: {subject}")
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,  # Let exceptions propagate for Celery retries
        )
        
        logger.info(f"✅ Welcome email sent successfully to {user.email}")
        return f"Welcome email sent to {user.email}"

    except User.DoesNotExist:
        logger.error(f"❌ User {user_id} not found for welcome email")
        return f"User {user_id} not found"
    except Exception as e:
        logger.warning(f"⚠️ Failed to send welcome email (attempt {self.request.retries + 1}/3): {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # 60, 120, 240 seconds
            logger.info(f"🔄 Retrying welcome email in {countdown} seconds...")
            raise self.retry(exc=e, countdown=countdown)
        else:
            logger.error(f"❌ Failed to send welcome email after {self.max_retries} attempts: {e}")
            return f"Failed to send welcome email after {self.max_retries} attempts: {str(e)}"


def send_welcome_email_robust(user_id):
    """Robust welcome email sender with fallback mechanisms"""
    try:
        # Try async first with Celery
        from celery import current_app
        try:
            # Check if Celery workers are active
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            
            if active_workers:
                send_welcome_email.delay(user_id)
                logger.info("✅ Welcome email queued via Celery")
                return "queued"
            else:
                logger.warning("⚠️ No active Celery workers found")
        except Exception as e:
            logger.warning(f"⚠️ Celery unavailable: {e}")
    except Exception as e:
        logger.error(f"❌ Error importing or initializing Celery: {e}")
    
    # Fallback to synchronous sending
    try:
        result = send_welcome_email(user_id)
        logger.info("✅ Welcome email sent synchronously")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email: {e}")
        return f"Failed to send welcome email: {str(e)}"


@shared_task
def send_verification_email(user_id):
    """Send email verification link (to be implemented)"""
    try:
        logger.info(f"📧 Queueing verification email for user {user_id}")
        # TODO: Implement email verification logic
        user = User.objects.get(id=user_id)
        logger.info(f"✅ Verification email queued for {user.email}")
        return f"Verification email queued for user {user_id}"
    except User.DoesNotExist:
        logger.error(f"❌ User {user_id} not found for verification email")
        return f"User {user_id} not found"
    except Exception as e:
        logger.error(f"❌ Failed to queue verification email: {e}")
        return f"Failed to queue verification email: {str(e)}"


@shared_task
def cleanup_inactive_users():
    """Clean up users who haven't verified their account after 7 days"""
    try:
        logger.info("🧹 Starting cleanup of inactive unverified users...")
        
        cutoff_date = timezone.now() - timedelta(days=7)
        inactive_users = User.objects.filter(
            is_verified=False,
            date_joined__lt=cutoff_date
        )

        count = inactive_users.count()
        
        if count > 0:
            user_emails = list(inactive_users.values_list('email', flat=True))
            logger.info(f"🗑️ Deleting {count} inactive users: {user_emails}")
            inactive_users.delete()
            logger.info(f"✅ Successfully cleaned up {count} inactive unverified users")
        else:
            logger.info("✅ No inactive users to clean up")
        
        return f"✅ Cleaned up {count} inactive unverified users"

    except Exception as e:
        logger.error(f"❌ Failed to clean up inactive users: {e}")
        return f"Failed to clean up inactive users: {str(e)}"


@shared_task
def validate_all_api_keys():
    """
    Scheduled task: validate all stored exchange API keys
    Used by Celery Beat to automatically check credentials daily/hourly
    """
    try:
        logger.info("🔑 Starting validation of all API keys...")
        
        active_api_keys = APIKey.objects.filter(is_active=True)
        exchange_service = ExchangeService()

        results = {
            "total": active_api_keys.count(),
            "validated": 0,
            "failed": 0,
            "details": []
        }

        logger.info(f"🔍 Found {results['total']} active API keys to validate")

        for api_key in active_api_keys:
            try:
                logger.debug(f"🔐 Validating API key for {api_key.exchange} (User: {api_key.user.username})")
                
                decrypted_keys = api_key.get_decrypted_keys()

                validation = exchange_service.test_api_key_connection(
                    exchange=api_key.exchange,
                    api_key=decrypted_keys["api_key"],
                    secret_key=decrypted_keys["secret_key"],
                    passphrase=decrypted_keys.get("passphrase")
                )

                if validation.get("connected", False):
                    api_key.mark_as_validated(True)
                    results["validated"] += 1
                    status = "valid"
                    logger.info(f"✅ API key validated successfully for {api_key.exchange} (User: {api_key.user.username})")
                else:
                    api_key.mark_as_validated(False)
                    results["failed"] += 1
                    status = "invalid"
                    error_msg = validation.get('error', 'Unknown error')
                    logger.warning(f"❌ API key validation failed for {api_key.exchange} (User: {api_key.user.username}): {error_msg}")

                results["details"].append({
                    "exchange": api_key.exchange,
                    "status": status,
                    "error": validation.get("error"),
                    "user": api_key.user.username,
                })

            except Exception as e:
                api_key.mark_as_validated(False)
                results["failed"] += 1
                results["details"].append({
                    "exchange": api_key.exchange,
                    "status": "error",
                    "error": str(e),
                    "user": api_key.user.username,
                })
                logger.error(f"💥 Exception validating API key for {api_key.exchange} (User: {api_key.user.username}): {e}")

        # Log summary
        logger.info(f"📊 API Key Validation Summary: {results['validated']} validated, {results['failed']} failed out of {results['total']} total")
        
        if results['failed'] > 0:
            logger.warning(f"⚠️ {results['failed']} API key validations failed. Check details for more information.")
        
        return results

    except Exception as e:
        logger.error(f"💥 Critical error in validate_all_api_keys task: {e}")
        return {
            "total": 0,
            "validated": 0,
            "failed": 0,
            "details": [],
            "error": str(e)
        }


@shared_task
def test_redis_connection():
    """Test Redis connection for debugging"""
    try:
        from django.core.cache import cache
        import redis
        
        # Test basic cache operations
        test_key = "redis_health_check"
        test_value = "ok"
        
        cache.set(test_key, test_value, 10)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            logger.info("✅ Redis connection test: SUCCESS")
            return {"status": "success", "message": "Redis is connected and working"}
        else:
            logger.error("❌ Redis connection test: FAILED - Data mismatch")
            return {"status": "failed", "message": "Redis data mismatch"}
            
    except redis.ConnectionError as e:
        logger.error(f"❌ Redis connection test: CONNECTION ERROR - {e}")
        return {"status": "error", "message": f"Redis connection error: {str(e)}"}
    except Exception as e:
        logger.error(f"❌ Redis connection test: UNKNOWN ERROR - {e}")
        return {"status": "error", "message": f"Unknown error: {str(e)}"}


@shared_task
def health_check():
    """Comprehensive health check for the users app"""
    try:
        health_info = {
            "timestamp": timezone.now().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # Check database connection
        try:
            user_count = User.objects.count()
            health_info["checks"]["database"] = {
                "status": "healthy",
                "users_count": user_count
            }
            logger.debug("✅ Database health check: SUCCESS")
        except Exception as e:
            health_info["checks"]["database"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_info["status"] = "degraded"
            logger.error(f"❌ Database health check: FAILED - {e}")
        
        # Check Redis connection
        try:
            from django.core.cache import cache
            cache.set("health_check", "ok", 1)
            if cache.get("health_check") == "ok":
                health_info["checks"]["redis"] = {"status": "healthy"}
                logger.debug("✅ Redis health check: SUCCESS")
            else:
                health_info["checks"]["redis"] = {"status": "unhealthy", "error": "Data mismatch"}
                health_info["status"] = "degraded"
                logger.error("❌ Redis health check: FAILED - Data mismatch")
        except Exception as e:
            health_info["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_info["status"] = "degraded"
            logger.error(f"❌ Redis health check: FAILED - {e}")
        
        # Check API key validation status
        try:
            total_keys = APIKey.objects.count()
            active_keys = APIKey.objects.filter(is_active=True).count()
            validated_keys = APIKey.objects.filter(is_active=True, is_validated=True).count()
            
            health_info["checks"]["api_keys"] = {
                "status": "healthy",
                "total": total_keys,
                "active": active_keys,
                "validated": validated_keys,
                "validation_rate": round((validated_keys / active_keys * 100) if active_keys > 0 else 0, 1)
            }
            logger.debug("✅ API Keys health check: SUCCESS")
        except Exception as e:
            health_info["checks"]["api_keys"] = {"status": "unhealthy", "error": str(e)}
            health_info["status"] = "degraded"
            logger.error(f"❌ API Keys health check: FAILED - {e}")
        
        logger.info(f"🏥 Health check completed: {health_info['status']}")
        return health_info
        
    except Exception as e:
        logger.error(f"💥 Health check task failed: {e}")
        return {
            "timestamp": timezone.now().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }