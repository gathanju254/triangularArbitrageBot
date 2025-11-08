# backend/apps/notifications/models.py
from django.db import models, transaction
from django.utils import timezone
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class NotificationManager(models.Manager):
    def unread(self):
        return self.filter(is_read=False)

    def for_user(self, user):
        return self.filter(user=user)

    def mark_all_read(self, user):
        return self.filter(user=user, is_read=False).update(is_read=True, read_at=timezone.now())


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('opportunity', 'Arbitrage Opportunity'),
        ('trade', 'Trade Execution'),
        ('risk', 'Risk Alert'),
        ('system', 'System Notification'),
        ('account', 'Account Notification'),
    ]

    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    DELIVERY_METHODS = {'email', 'push', 'in_app'}

    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict)  # Additional data

    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    # Delivery
    delivery_methods = models.JSONField(default=list)  # ['email', 'push', 'in_app']
    sent_via = models.JSONField(default=list)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    objects = NotificationManager()

    def clean(self):
        # Ensure delivery_methods contains only allowed methods
        if self.delivery_methods:
            invalid = [m for m in self.delivery_methods if m not in self.DELIVERY_METHODS]
            if invalid:
                raise ValueError(f"Invalid delivery methods: {invalid}")

    def save(self, *args, **kwargs):
        # Ensure sent_via contains unique methods and validate delivery methods
        if self.sent_via is None:
            self.sent_via = []
        else:
            # de-duplicate preserving order
            seen = set()
            deduped = []
            for m in self.sent_via:
                if m not in seen:
                    deduped.append(m)
                    seen.add(m)
            self.sent_via = deduped

        # Validate delivery methods
        if self.delivery_methods is None:
            self.delivery_methods = []
        else:
            invalid = [m for m in self.delivery_methods if m not in self.DELIVERY_METHODS]
            if invalid:
                raise ValueError(f"Invalid delivery methods: {invalid}")

        # Use transaction to avoid partial writes when updating timestamps
        with transaction.atomic():
            super().save(*args, **kwargs)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.title} - {self.user}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save()

    def mark_as_sent(self, method: str):
        """Mark notification as sent via specific method"""
        now = timezone.now()
        changed = False
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = now
            changed = True

        if method and method not in (self.sent_via or []):
            self.sent_via = (self.sent_via or []) + [method]
            changed = True

        if changed:
            self.save()

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'is_sent': self.is_sent,
            'delivery_methods': self.delivery_methods,
            'sent_via': self.sent_via,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
        }

    def send(self, methods: List[str] = None) -> None:
        """
        Helper to request sending this notification via the given methods.
        This method defers actual delivery to the notifications service/tasks to avoid
        importing service-level code at import time. It will try to call
        `apps.notifications.services.NotificationService.send_notification` if available.
        """
        # Validate requested methods
        methods = methods or self.delivery_methods or []
        invalid = [m for m in methods if m not in self.DELIVERY_METHODS]
        if invalid:
            raise ValueError(f"Invalid delivery methods requested: {invalid}")

        # Import service lazily to avoid circular imports at module import time
        try:
            from .services import NotificationService
        except Exception:
            logger.debug("NotificationService not available; skipping immediate send for notification id=%s", getattr(self, 'id', None))
            return

        # Call service (it should handle background tasks)
        try:
            NotificationService.send_notification(self, methods=methods)
        except Exception:
            logger.exception("Failed to request send for Notification id=%s", getattr(self, 'id', None))