# backend/apps/notifications/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_email_notification(notification_id):
    """
    Send email notification asynchronously.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if 'email' not in notification.delivery_methods:
            logger.info(f"Email delivery not requested for notification {notification_id}")
            return
        
        if notification.is_sent:
            logger.info(f"Notification {notification_id} already sent")
            return
        
        subject = f"[{notification.get_priority_display()}] {notification.title}"
        
        # Build email message
        message = f"""
        {notification.message}
        
        Notification Type: {notification.get_notification_type_display()}
        Priority: {notification.get_priority_display()}
        
        ---
        This is an automated message from {settings.PROJECT_NAME}
        """
        
        # Add additional data if present
        if notification.data:
            message += f"\nAdditional Data: {notification.data}"
        
        try:
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                fail_silently=False,
            )
            
            # Update notification status
            notification.is_sent = True
            notification.sent_at = timezone.now()
            if 'email' not in notification.sent_via:
                notification.sent_via.append('email')
            notification.save()
            
            logger.info(f"Email notification {notification_id} sent successfully to {notification.user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification {notification_id}: {str(e)}")
            raise
    
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
    except Exception as e:
        logger.error(f"Error processing email notification {notification_id}: {str(e)}")
        raise

@shared_task
def send_bulk_email_notifications(notification_ids):
    """
    Send multiple email notifications in bulk.
    """
    for notification_id in notification_ids:
        send_email_notification.delay(notification_id)

@shared_task
def process_pending_notifications():
    """
    Process all pending notifications that haven't been sent yet.
    """
    pending_notifications = Notification.objects.filter(
        is_sent=False,
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)  # Last 24 hours
    )
    
    for notification in pending_notifications:
        if 'email' in notification.delivery_methods:
            send_email_notification.delay(notification.id)
        
        # For other delivery methods (push, etc.), add similar logic here
        # if 'push' in notification.delivery_methods:
        #     send_push_notification.delay(notification.id)
    
    logger.info(f"Processed {pending_notifications.count()} pending notifications")

@shared_task
def cleanup_old_notifications(days_old=30):
    """
    Clean up notifications older than specified days.
    """
    from django.db.models import Q
    
    cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
    
    # Delete read notifications older than cutoff date
    deleted_count, _ = Notification.objects.filter(
        Q(is_read=True) & Q(created_at__lt=cutoff_date)
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} notifications older than {days_old} days")
    
    return deleted_count

@shared_task
def send_digest_notification(user_id, notification_data):
    """
    Send digest notification containing multiple updates.
    """
    from apps.users.models import User
    
    try:
        user = User.objects.get(id=user_id)
        
        # Create digest notification
        notification = Notification.objects.create(
            user=user,
            notification_type='system',
            priority='medium',
            title='Daily Trading Digest',
            message=notification_data.get('message', 'Your daily trading summary'),
            data=notification_data,
            delivery_methods=['email', 'in_app']
        )
        
        # Send immediately
        send_email_notification.delay(notification.id)
        
        logger.info(f"Digest notification sent to user {user_id}")
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for digest notification")
    except Exception as e:
        logger.error(f"Error sending digest notification to user {user_id}: {str(e)}")