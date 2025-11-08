# backend/apps/users/validators.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView

from ..models import Notification
from ..services import NotificationService

@method_decorator(login_required, name='dispatch')
class NotificationWebView(ListView):
    """
    Web view for user notifications
    """
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        context['stats'] = NotificationService.get_notification_stats(self.request.user)
        return context

@login_required
def mark_all_read_web(request):
    """
    Web view to mark all notifications as read
    """
    if request.method == 'POST':
        updated_count = NotificationService.mark_notifications_read(request.user)
        return redirect('notifications:list')
    
    return redirect('notifications:list')

@login_required
def notification_detail(request, pk):
    """
    Web view for notification detail
    """
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        
        # Mark as read when viewing
        if not notification.is_read:
            notification.mark_as_read()
        
        return render(request, 'notifications/detail.html', {
            'notification': notification
        })
    except Notification.DoesNotExist:
        return redirect('notifications:list')