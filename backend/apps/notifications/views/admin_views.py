# backend/apps/users/validators.py
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from ..models import Notification

@method_decorator(staff_member_required, name='dispatch')
class NotificationAdminView(TemplateView):
    """
    Admin view for system-wide notification management
    """
    template_name = 'admin/notifications/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # System-wide statistics
        total_notifications = Notification.objects.count()
        sent_notifications = Notification.objects.filter(is_sent=True).count()
        read_notifications = Notification.objects.filter(is_read=True).count()
        
        # Recent activity (last 24 hours)
        yesterday = timezone.now() - timedelta(days=1)
        recent_notifications = Notification.objects.filter(
            created_at__gte=yesterday
        ).count()
        
        # Notification types distribution
        type_distribution = Notification.objects.values(
            'notification_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Priority distribution
        priority_distribution = Notification.objects.values(
            'priority'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        context.update({
            'total_notifications': total_notifications,
            'sent_notifications': sent_notifications,
            'read_notifications': read_notifications,
            'pending_notifications': total_notifications - sent_notifications,
            'unread_notifications': total_notifications - read_notifications,
            'recent_notifications': recent_notifications,
            'type_distribution': type_distribution,
            'priority_distribution': priority_distribution,
        })
        
        return context

@staff_member_required
def admin_notification_stats(request):
    """
    Detailed admin statistics view
    """
    # Time-based statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    today_count = Notification.objects.filter(created_at__date=today).count()
    week_count = Notification.objects.filter(created_at__date__gte=week_ago).count()
    month_count = Notification.objects.filter(created_at__date__gte=month_ago).count()
    
    # Delivery statistics
    delivery_stats = {
        'email_sent': Notification.objects.filter(sent_via__contains=['email']).count(),
        'push_sent': Notification.objects.filter(sent_via__contains=['push']).count(),
        'in_app_only': Notification.objects.filter(
            delivery_methods=['in_app']
        ).count(),
    }
    
    return render(request, 'admin/notifications/stats.html', {
        'today_count': today_count,
        'week_count': week_count,
        'month_count': month_count,
        'delivery_stats': delivery_stats,
    })