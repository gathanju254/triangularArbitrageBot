# backend/apps/risk_management/serializers.py
from rest_framework import serializers
from .models import RiskConfig, RiskMetrics, TradeLimit

class RiskConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskConfig
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class RiskMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskMetrics
        fields = '__all__'
        read_only_fields = ('user', 'date')

class TradeLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeLimit
        fields = '__all__'
        read_only_fields = ('user', 'current_value', 'is_breached', 'breached_at')

class RiskOverviewSerializer(serializers.Serializer):
    total_pnl = serializers.DecimalField(max_digits=12, decimal_places=2)
    daily_pnl = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_limits = serializers.IntegerField()
    breached_limits = serializers.IntegerField()
    risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)