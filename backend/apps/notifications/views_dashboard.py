# backend/apps/notifications/views_dashboard.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Notification

class NotificationsDashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Notification statistics
        user_notifications = Notification.objects.filter(user=user)
        
        stats = {
            'notification_stats': {
                'total': user_notifications.count(),
                'unread': user_notifications.filter(is_read=False).count(),
                'read': user_notifications.filter(is_read=True).count(),
                'recent_24h': user_notifications.filter(
                    created_at__gte=twenty_four_hours_ago
                ).count(),
                'recent_week': user_notifications.filter(
                    created_at__gte=seven_days_ago
                ).count()
            },
            'notification_types': {
                'trade_alerts': user_notifications.filter(
                    notification_type='trade_alert'
                ).count(),
                'risk_alerts': user_notifications.filter(
                    notification_type='risk_alert'
                ).count(),
                'opportunity_alerts': user_notifications.filter(
                    notification_type='opportunity_alert'
                ).count(),
                'system_alerts': user_notifications.filter(
                    notification_type='system_alert'
                ).count()
            },
            'recent_alerts': list(
                user_notifications.filter(
                    is_read=False,
                    priority__in=['high', 'medium']
                ).order_by('-created_at')[:5].values(
                    'id', 'title', 'message', 'notification_type', 'priority', 'created_at'
                )
            ),
            'settings': {
                'email_notifications': getattr(user, 'email_notifications', True),
                'push_notifications': getattr(user, 'push_notifications', True),
                'trade_alerts': getattr(user, 'trade_alerts', True),
                'risk_alerts': getattr(user, 'risk_alerts', True)
            }
        }
        
        return Response(stats)