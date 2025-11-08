# backend/apps/notifications/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    read_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_email', 'user_username', 'notification_type',
            'priority', 'title', 'message', 'data', 'is_read', 'is_sent',
            'delivery_methods', 'sent_via', 'created_at', 'read_at', 'sent_at',
            'created_at_formatted', 'read_at_formatted'
        ]
        read_only_fields = [
            'id', 'created_at', 'read_at', 'sent_at', 'is_sent', 'sent_via'
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S') if obj.created_at else None
    
    def get_read_at_formatted(self, obj):
        return obj.read_at.strftime('%Y-%m-%d %H:%M:%S') if obj.read_at else None

class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'user', 'notification_type', 'priority', 'title', 'message',
            'data', 'delivery_methods'
        ]
    
    def validate_delivery_methods(self, value):
        valid_methods = ['email', 'push', 'in_app']
        for method in value:
            if method not in valid_methods:
                raise serializers.ValidationError(
                    f"Invalid delivery method: {method}. Must be one of {valid_methods}"
                )
        return value

class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['is_read']
    
    def update(self, instance, validated_data):
        is_read = validated_data.get('is_read', instance.is_read)
        
        if is_read and not instance.is_read:
            instance.read_at = timezone.now()
        elif not is_read and instance.is_read:
            instance.read_at = None
        
        instance.is_read = is_read
        instance.save()
        return instance

class NotificationStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    read = serializers.IntegerField()
    by_type = serializers.DictField()
    by_priority = serializers.DictField()