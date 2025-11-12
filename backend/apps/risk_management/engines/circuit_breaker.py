# backend/apps/risk_management/engines/circuit_breaker.py
from django.utils import timezone
from apps.notifications.services import NotificationService

class CircuitBreaker:
    def __init__(self):
        self.triggered_users = set()

    def trigger(self, user, reason):
        """Trigger circuit breaker for user"""
        self.triggered_users.add(user.id)
        
        # Send immediate notification
        NotificationService.send_circuit_breaker_alert(user, reason)
        
        # Log the event
        self._log_trigger(user, reason)
        
        return True

    def release(self, user):
        """Release circuit breaker for user"""
        if user.id in self.triggered_users:
            self.triggered_users.remove(user.id)
            NotificationService.send_circuit_breaker_release(user)
            return True
        return False

    def is_triggered(self, user):
        """Check if circuit breaker is triggered for user"""
        return user.id in self.triggered_users

    def _log_trigger(self, user, reason):
        """Log circuit breaker trigger event"""
        from ..models import RiskMetrics
        today = timezone.now().date()
        
        RiskMetrics.objects.update_or_create(
            user=user,
            date=today,
            defaults={'circuit_breaker_triggered': True}
        )