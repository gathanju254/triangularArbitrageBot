# backend/apps/notifications/views/api_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q
from django.core.cache import cache

from ..models import Notification
from ..serializers import (
    NotificationSerializer, 
    NotificationCreateSerializer,
    NotificationUpdateSerializer,
    NotificationStatsSerializer
)
from ..services import NotificationService

class NotificationDebugView(APIView):
    """
    Debug view to test notification functionality
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Test creating a notification
        notification = Notification.objects.create(
            user=request.user,
            notification_type='system',
            priority='medium',
            title='Test Notification',
            message='This is a test notification to verify the system is working.',
            delivery_methods=['in_app']
        )
        
        # Get user notifications
        user_notifications = Notification.objects.filter(user=request.user)
        
        return Response({
            'debug': True,
            'notification_created': notification.id,
            'total_notifications': user_notifications.count(),
            'unread_count': user_notifications.filter(is_read=False).count(),
            'recent_notifications': NotificationSerializer(
                user_notifications.order_by('-created_at')[:5], 
                many=True
            ).data
        })

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NotificationUpdateSerializer
        return NotificationSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get unread notifications for the current user.
        """
        unread_notifications = self.get_queryset().filter(is_read=False)
        page = self.paginate_queryset(unread_notifications)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read for the current user.
        """
        updated_count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark a specific notification as read.
        """
        notification = self.get_object()
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """
        Mark a specific notification as unread.
        """
        notification = self.get_object()
        
        if notification.is_read:
            notification.is_read = False
            notification.read_at = None
            notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get notification statistics for the current user.
        """
        cache_key = f"notification_stats_{request.user.id}"
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        unread = queryset.filter(is_read=False).count()
        read = total - unread
        
        # Count by notification type
        by_type = queryset.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Count by priority
        by_priority = queryset.values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats = {
            'total': total,
            'unread': unread,
            'read': read,
            'by_type': {item['notification_type']: item['count'] for item in by_type},
            'by_priority': {item['priority']: item['count'] for item in by_priority},
        }
        
        serializer = NotificationStatsSerializer(stats)
        
        # Cache for 5 minutes
        cache.set(cache_key, serializer.data, 300)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent notifications (last 7 days).
        """
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        recent_notifications = self.get_queryset().filter(
            created_at__gte=seven_days_ago
        )
        
        page = self.paginate_queryset(recent_notifications)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(recent_notifications, many=True)
        return Response(serializer.data)

class AdminNotificationViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing all notifications (admin only).
    """
    # Use the IsAdminUser permission from users app
    from apps.users.permissions import IsAdminUser
    
    permission_classes = [IsAdminUser]
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def system_stats(self, request):
        """
        Get system-wide notification statistics.
        """
        from datetime import datetime, timedelta
        
        # Total stats
        total = Notification.objects.count()
        sent = Notification.objects.filter(is_sent=True).count()
        read = Notification.objects.filter(is_read=True).count()
        
        # Today's stats
        today = timezone.now().date()
        today_count = Notification.objects.filter(created_at__date=today).count()
        
        # Last 7 days trend
        last_7_days = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = Notification.objects.filter(created_at__date=date).count()
            last_7_days.append({
                'date': date.isoformat(),
                'count': count
            })
        
        # By type and priority
        by_type = Notification.objects.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        by_priority = Notification.objects.values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats = {
            'total': total,
            'sent': sent,
            'read': read,
            'pending': total - sent,
            'unread': total - read,
            'today': today_count,
            'trend_7_days': last_7_days,
            'by_type': {item['notification_type']: item['count'] for item in by_type},
            'by_priority': {item['priority']: item['count'] for item in by_priority},
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """
        Bulk delete notifications (admin only).
        """
        notification_ids = request.data.get('notification_ids', [])
        
        if not notification_ids:
            return Response(
                {'error': 'No notification IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count, _ = Notification.objects.filter(id__in=notification_ids).delete()
        
        return Response({
            'message': f'Successfully deleted {deleted_count} notifications',
            'deleted_count': deleted_count
        })
    
    @action(detail=False, methods=['post'])
    def bulk_mark_read(self, request):
        """
        Bulk mark notifications as read (admin only).
        """
        notification_ids = request.data.get('notification_ids', [])
        
        if not notification_ids:
            return Response(
                {'error': 'No notification IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_count = Notification.objects.filter(id__in=notification_ids).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'Successfully marked {updated_count} notifications as read',
            'updated_count': updated_count
        })

class TestNotificationView(APIView):
    """
    View for testing notification delivery.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        notification_type = request.data.get('type', 'system')
        message = request.data.get('message', 'Test notification')
        priority = request.data.get('priority', 'medium')
        
        notification = Notification.objects.create(
            user=request.user,
            notification_type=notification_type,
            priority=priority,
            title='Test Notification',
            message=message,
            delivery_methods=['in_app']
        )
        
        return Response({
            'message': 'Test notification created',
            'notification_id': notification.id,
            'notification_type': notification_type,
            'priority': priority
        })