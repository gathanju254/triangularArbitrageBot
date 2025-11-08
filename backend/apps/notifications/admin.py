# backend/apps/notifications/admin.py

from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'notification_type', 'priority', 'title', 
        'is_read', 'is_sent', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'is_sent', 'created_at'
    ]
    search_fields = ['title', 'message', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'read_at', 'sent_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'notification_type', 'priority')
        }),
        ('Content', {
            'fields': ('title', 'message', 'data')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'read_at', 'sent_at')
        }),
        ('Delivery', {
            'fields': ('delivery_methods', 'sent_via')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(is_sent=True)
        self.message_user(request, f'{updated} notifications marked as sent.')
    
    actions = [mark_as_read, mark_as_unread, mark_as_sent]