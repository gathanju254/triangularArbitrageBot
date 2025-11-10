# backend/apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile, APIKey, UserSettings, BotConfiguration

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Additional Info'), {'fields': ('user_type', 'phone', 'timezone', 'is_verified')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Additional Info'), {'fields': ('user_type', 'phone', 'timezone')}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'risk_tolerance', 'max_daily_loss', 'max_position_size')
    list_filter = ('risk_tolerance',)

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'exchange', 'label', 'is_active', 'is_validated', 'created_at')
    list_filter = ('exchange', 'is_active', 'is_validated')
    search_fields = ('user__username', 'label')

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'trading_mode', 'risk_tolerance', 'created_at')
    list_filter = ('trading_mode', 'risk_tolerance')
    fieldsets = (
        ('Trading Settings', {
            'fields': (
                'user',
                'trading_mode',
                'max_concurrent_trades',
                'min_trade_amount',
                'slippage_tolerance',
            )
        }),
        ('Risk Management', {
            'fields': (
                'risk_tolerance',
                'max_daily_loss',
                'max_position_size',
                'max_drawdown',
                'stop_loss_enabled',
                'stop_loss_percent',
                'take_profit_enabled',
                'take_profit_percent',
            )
        }),
        ('Notifications', {
            'fields': (
                'email_notifications',
                'push_notifications',
                'trading_alerts',
                'risk_alerts',
            )
        }),
        ('Exchange Settings', {
            'fields': (
                'preferred_exchanges',
                'min_profit_threshold',
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_at',
                'updated_at',
                'last_modified_by',
            ),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BotConfiguration)
class BotConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_balance',
        'trade_size_fraction',
        'trading_enabled',
        'auto_restart',
        'updated_at',
    )
    search_fields = ('enabled_exchanges',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-id',)
    fieldsets = (
        ('Balances & Sizing', {
            'fields': (
                'base_balance',
                'trade_size_fraction',
            )
        }),
        ('Trading & Execution', {
            'fields': (
                'trading_enabled',
                'auto_restart',
                'enabled_exchanges',
            )
        }),
        ('System Settings', {
            'fields': (
                'health_check_interval',
                'data_retention_days',
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def enabled_exchanges_display(self, obj):
        try:
            ex = obj.enabled_exchanges or []
            return ", ".join(ex) if isinstance(ex, (list, tuple)) else str(ex)
        except Exception:
            return str(obj.enabled_exchanges)
    enabled_exchanges_display.short_description = 'Enabled Exchanges'

    def has_add_permission(self, request):
        # Only allow one instance
        return not BotConfiguration.objects.exists()