# backend/apps/users/serializers/settings_serializers.py
from rest_framework import serializers
from ..models.settings import UserSettings, BotConfiguration

class TradingSettingsSerializer(serializers.ModelSerializer):
    auto_trading = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSettings
        fields = [
            'trading_mode',
            'max_concurrent_trades', 
            'min_trade_amount',
            'slippage_tolerance',
            'auto_trading'
        ]
    
    def get_auto_trading(self, obj):
        return obj.trading_mode != 'manual'

class RiskSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            'risk_tolerance',
            'max_daily_loss',
            'max_position_size',
            'max_drawdown',
            'stop_loss_enabled',
            'take_profit_enabled',
            'stop_loss_percent',
            'take_profit_percent'
        ]

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            'email_notifications',
            'push_notifications',
            'trading_alerts',
            'risk_alerts'
        ]

class ExchangeSettingsSerializer(serializers.ModelSerializer):
    enabled_exchanges = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSettings
        fields = [
            'preferred_exchanges',
            'min_profit_threshold',
            'enabled_exchanges'
        ]
    
    def get_enabled_exchanges(self, obj):
        from ..services.settings_service import SettingsService
        bot_config = SettingsService.get_bot_configuration()
        return bot_config.enabled_exchanges

class UserSettingsSerializer(serializers.ModelSerializer):
    """Complete user settings serializer"""
    trading = serializers.SerializerMethodField()
    risk = serializers.SerializerMethodField()
    notifications = serializers.SerializerMethodField()
    exchanges = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSettings
        fields = [
            'trading',
            'risk', 
            'notifications',
            'exchanges',
            'created_at',
            'updated_at'
        ]
    
    def get_trading(self, obj):
        return TradingSettingsSerializer(obj).data
    
    def get_risk(self, obj):
        return RiskSettingsSerializer(obj).data
    
    def get_notifications(self, obj):
        return NotificationSettingsSerializer(obj).data
    
    def get_exchanges(self, obj):
        return ExchangeSettingsSerializer(obj).data

class BotConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotConfiguration
        fields = [
            'base_balance',
            'trade_size_fraction',
            'auto_restart',
            'trading_enabled',
            'enabled_exchanges',
            'health_check_interval',
            'data_retention_days'
        ]