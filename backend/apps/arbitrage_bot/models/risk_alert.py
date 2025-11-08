# backend/apps/arbitrage_bot/models/risk_alert.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

class RiskAlert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    message = models.TextField()
    metric = models.CharField(max_length=100, blank=True, null=True)
    value = models.FloatField(blank=True, null=True)
    threshold = models.FloatField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'risk_alerts'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"RiskAlert {self.id} - {self.alert_type} - {self.severity}"
    
    def mark_resolved(self):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save()