# backend/apps/notifications/services.py

from django.utils import timezone
from django.db.models import Q
from .models import Notification
from .tasks import send_email_notification

class NotificationService:
    
    @staticmethod
    def send_opportunity_alert(opportunity):
        """Create notification for a new arbitrage opportunity in TAB"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
            
            if user:
                triangle_str = ' → '.join(opportunity.triangle) if isinstance(opportunity.triangle, list) else str(opportunity.triangle)
                
                notification = Notification.objects.create(
                    user=user,
                    notification_type='opportunity',
                    priority='high' if opportunity.profit_percentage >= 3.0 else 'medium',
                    title='ARBITRAGE - New Opportunity',
                    message=f'{triangle_str}: {opportunity.profit_percentage:.2f}% potential profit',
                    data={
                        'opportunity_id': getattr(opportunity, 'id', None),
                        'profit_percentage': float(opportunity.profit_percentage),
                        'triangle': opportunity.triangle,
                        'timestamp': timezone.now().isoformat()
                    },
                    delivery_methods=['in_app', 'email']
                )
                
                send_email_notification.delay(notification.id)
                return notification
        except Exception as e:
            print(f"Error sending opportunity alert: {e}")
        return None

    @staticmethod
    def send_trade_completion_alert(trade_execution):
        """Create notification for completed trade execution in TAB"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
            
            if user:
                notification_type = 'trade'
                priority = 'medium'
                
                if trade_execution.profit > 0:
                    title = "SUCCESS - Trade Profit"
                    message = f"Trade completed with ${trade_execution.profit:.2f} profit"
                else:
                    title = "WARNING - Trade Loss"
                    message = f"Trade completed with ${abs(trade_execution.profit):.2f} loss"
                    priority = 'high'
                
                notification = Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    priority=priority,
                    title=title,
                    message=message,
                    data={
                        'trade_id': getattr(trade_execution, 'id', None),
                        'profit': float(trade_execution.profit),
                        'profit_percentage': float(trade_execution.profit_percentage),
                        'exchange': getattr(trade_execution, 'exchange', 'unknown'),
                        'timestamp': timezone.now().isoformat()
                    },
                    delivery_methods=['in_app']
                )
                
                if priority == 'high':
                    send_email_notification.delay(notification.id)
                    
                return notification
        except Exception as e:
            print(f"Error sending trade completion alert: {e}")
        return None

    @staticmethod
    def send_risk_alert(user, risk_type, message, data=None):
        """Create risk-related notification"""
        priority_map = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high', 
            'critical': 'critical'
        }
        
        try:
            notification = Notification.objects.create(
                user=user,
                notification_type='risk',
                priority=priority_map.get(risk_type, 'medium'),
                title=f'RISK ALERT: {risk_type.title()}',
                message=message,
                data=data or {},
                delivery_methods=['in_app', 'email']
            )
            
            # Send email for medium and higher priority risk alerts
            if risk_type in ['medium', 'high', 'critical']:
                send_email_notification.delay(notification.id)
            
            return notification
        except Exception as e:
            print(f"Error sending risk alert: {e}")
            return None

    @staticmethod
    def send_system_notification(user, title, message, data=None, priority='medium'):
        """Create system notification"""
        try:
            notification = Notification.objects.create(
                user=user,
                notification_type='system',
                priority=priority,
                title=title,
                message=message,
                data=data or {},
                delivery_methods=['in_app']
            )
            
            return notification
        except Exception as e:
            print(f"Error sending system notification: {e}")
            return None

    @staticmethod
    def send_account_notification(user, title, message, data=None):
        """Create account-related notification"""
        try:
            notification = Notification.objects.create(
                user=user,
                notification_type='account',
                priority='medium',
                title=title,
                message=message,
                data=data or {},
                delivery_methods=['in_app', 'email']
            )
            
            send_email_notification.delay(notification.id)
            return notification
        except Exception as e:
            print(f"Error sending account notification: {e}")
            return None

    @staticmethod
    def send_bot_status_notification(status, message, data=None):
        """Create bot status notification for all admin users"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            admin_users = User.objects.filter(is_staff=True)
            notifications = []
            
            title_map = {
                'started': 'BOT STARTED - Triangular Arbitrage Bot',
                'stopped': 'BOT STOPPED - Triangular Arbitrage Bot', 
                'error': 'BOT ERROR - Triangular Arbitrage Bot',
                'warning': 'BOT WARNING - Triangular Arbitrage Bot'
            }
            
            priority_map = {
                'started': 'medium',
                'stopped': 'medium',
                'error': 'high',
                'warning': 'medium'
            }
            
            title = title_map.get(status, f"BOT {status.upper()} - Triangular Arbitrage Bot")
            priority = priority_map.get(status, 'medium')
            
            for user in admin_users:
                notification = Notification.objects.create(
                    user=user,
                    notification_type='system',
                    priority=priority,
                    title=title,
                    message=message,
                    data=data or {'bot_status': status},
                    delivery_methods=['in_app', 'email']
                )
                notifications.append(notification)
                
                # Send email for important bot status changes
                if status in ['error', 'started', 'stopped']:
                    send_email_notification.delay(notification.id)
            
            return notifications
        except Exception as e:
            print(f"Error sending bot status notification: {e}")
            return []

    @staticmethod
    def send_exchange_connection_notification(exchange_name, status, message):
        """Create exchange connection status notification"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            admin_users = User.objects.filter(is_staff=True)
            notifications = []
            
            title = f"EXCHANGE {status.upper()} - {exchange_name}"
            priority = 'high' if status == 'disconnected' else 'medium'
            
            for user in admin_users:
                notification = Notification.objects.create(
                    user=user,
                    notification_type='system',
                    priority=priority,
                    title=title,
                    message=message,
                    data={
                        'exchange': exchange_name,
                        'status': status,
                        'timestamp': timezone.now().isoformat()
                    },
                    delivery_methods=['in_app', 'email']
                )
                notifications.append(notification)
                
                if status == 'disconnected':
                    send_email_notification.delay(notification.id)
            
            return notifications
        except Exception as e:
            print(f"Error sending exchange connection notification: {e}")
            return []

    @staticmethod
    def get_user_notifications(user, filters=None):
        """Get notifications for a user with optional filtering"""
        try:
            queryset = Notification.objects.filter(user=user).order_by('-created_at')
            
            if filters:
                if filters.get('unread_only'):
                    queryset = queryset.filter(is_read=False)
                if filters.get('notification_type'):
                    queryset = queryset.filter(notification_type=filters['notification_type'])
                if filters.get('priority'):
                    queryset = queryset.filter(priority=filters['priority'])
                if filters.get('date_from'):
                    queryset = queryset.filter(created_at__gte=filters['date_from'])
                if filters.get('date_to'):
                    queryset = queryset.filter(created_at__lte=filters['date_to'])
            
            return queryset
        except Exception as e:
            print(f"Error getting user notifications: {e}")
            return Notification.objects.none()

    @staticmethod
    def mark_notifications_read(user, notification_ids=None):
        """Mark notifications as read"""
        try:
            queryset = Notification.objects.filter(user=user, is_read=False)
            
            if notification_ids:
                queryset = queryset.filter(id__in=notification_ids)
            
            updated_count = queryset.update(is_read=True, read_at=timezone.now())
            return updated_count
        except Exception as e:
            print(f"Error marking notifications as read: {e}")
            return 0

    @staticmethod
    def get_notification_stats(user):
        """Get notification statistics for a user"""
        from django.db.models import Count
        
        try:
            stats = Notification.objects.filter(user=user).aggregate(
                total=Count('id'),
                unread=Count('id', filter=Q(is_read=False)),
                read=Count('id', filter=Q(is_read=True))
            )
            
            # Add counts by type
            by_type = Notification.objects.filter(user=user).values(
                'notification_type'
            ).annotate(count=Count('id')).order_by('-count')
            
            stats['by_type'] = {item['notification_type']: item['count'] for item in by_type}
            
            # Add counts by priority
            by_priority = Notification.objects.filter(user=user).values(
                'priority'
            ).annotate(count=Count('id')).order_by('-count')
            
            stats['by_priority'] = {item['priority']: item['count'] for item in by_priority}
            
            return stats
        except Exception as e:
            print(f"Error getting notification stats: {e}")
            return {
                'total': 0,
                'unread': 0,
                'read': 0,
                'by_type': {},
                'by_priority': {}
            }

    @staticmethod
    def cleanup_old_notifications(days=30):
        """Clean up old notifications"""
        from datetime import timedelta
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Delete read notifications older than cutoff date
            deleted_count, _ = Notification.objects.filter(
                is_read=True,
                created_at__lt=cutoff_date
            ).delete()
            
            return deleted_count
        except Exception as e:
            print(f"Error cleaning up old notifications: {e}")
            return 0

    @staticmethod
    def bulk_create_notifications(notifications_data):
        """Bulk create notifications for multiple users"""
        try:
            notifications = []
            for data in notifications_data:
                notification = Notification(**data)
                notifications.append(notification)
            
            created_notifications = Notification.objects.bulk_create(notifications)
            return created_notifications
        except Exception as e:
            print(f"Error bulk creating notifications: {e}")
            return []

    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for a user"""
        try:
            return Notification.objects.filter(user=user, is_read=False).count()
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0

    @staticmethod
    def send_balance_alert(user, exchange, balance_info):
        """Create balance-related notification"""
        try:
            notification = Notification.objects.create(
                user=user,
                notification_type='account',
                priority='medium',
                title='BALANCE UPDATE',
                message=f'{exchange} balance: ${balance_info.get("total_balance", 0):.2f}',
                data={
                    'exchange': exchange,
                    'total_balance': float(balance_info.get('total_balance', 0)),
                    'available_balance': float(balance_info.get('available_balance', 0)),
                    'timestamp': timezone.now().isoformat()
                },
                delivery_methods=['in_app']
            )
            
            return notification
        except Exception as e:
            print(f"Error sending balance alert: {e}")
            return None