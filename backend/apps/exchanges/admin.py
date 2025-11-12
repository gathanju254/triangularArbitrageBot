# backend/apps/exchanges/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Exchange, MarketData, ExchangeCredentials


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    """Admin interface for Exchange model"""
    
    list_display = [
        'name', 'code', 'exchange_type', 'is_active', 'trading_fee', 
        'rate_limit', 'supported_pairs_count', 'created_at'
    ]
    list_filter = ['exchange_type', 'is_active', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'name', 'code', 'exchange_type', 'is_active'
            ]
        }),
        ('API Configuration', {
            'fields': [
                'base_url', 'api_documentation', 'rate_limit'
            ]
        }),
        ('Fee Information', {
            'fields': [
                'trading_fee', 'withdrawal_fee'
            ]
        }),
        ('Trading Information', {
            'fields': [
                'precision_info', 'supported_pairs'
            ]
        }),
        ('Timestamps', {
            'fields': ['created_at'],
            'classes': ['collapse']
        })
    ]
    
    def supported_pairs_count(self, obj):
        """Display count of supported pairs"""
        return len(obj.supported_pairs) if obj.supported_pairs else 0
    supported_pairs_count.short_description = 'Supported Pairs'


@admin.register(MarketData)
class MarketDataAdmin(admin.ModelAdmin):
    """Admin interface for MarketData model"""
    
    list_display = [
        'symbol', 'exchange', 'bid_price', 'ask_price', 'last_price',
        'volume_24h', 'spread', 'timestamp', 'is_fresh'
    ]
    list_filter = ['exchange', 'symbol', 'timestamp', 'is_fresh']
    search_fields = ['symbol', 'exchange__name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = [
        ('Market Information', {
            'fields': [
                'exchange', 'symbol'
            ]
        }),
        ('Price Data', {
            'fields': [
                'bid_price', 'ask_price', 'last_price', 'spread'
            ]
        }),
        ('Volume Data', {
            'fields': [
                'volume_24h'
            ]
        }),
        ('Status', {
            'fields': [
                'timestamp', 'is_fresh'
            ]
        })
    ]
    
    def get_queryset(self, request):
        """Optimize queryset with related objects"""
        return super().get_queryset(request).select_related('exchange')


@admin.register(ExchangeCredentials)
class ExchangeCredentialsAdmin(admin.ModelAdmin):
    """Admin interface for ExchangeCredentials model"""
    
    list_display = [
        'user', 'exchange', 'is_validated', 'trading_enabled', 
        'withdrawal_enabled', 'last_validation'
    ]
    list_filter = [
        'exchange', 'is_validated', 'trading_enabled', 
        'withdrawal_enabled', 'last_validation'
    ]
    search_fields = [
        'user__username', 'user__email', 'exchange__name'
    ]
    readonly_fields = ['last_validation']
    
    fieldsets = [
        ('User & Exchange', {
            'fields': [
                'user', 'exchange', 'api_key'
            ]
        }),
        ('Validation Status', {
            'fields': [
                'is_validated', 'validation_message', 'last_validation'
            ]
        }),
        ('Permissions', {
            'fields': [
                'trading_enabled', 'withdrawal_enabled'
            ]
        })
    ]
    
    def get_queryset(self, request):
        """Optimize queryset with related objects"""
        return super().get_queryset(request).select_related(
            'user', 'exchange', 'api_key'
        )
    
    actions = ['validate_credentials', 'enable_trading', 'disable_trading']
    
    def validate_credentials(self, request, queryset):
        """Admin action to validate selected credentials"""
        for credential in queryset:
            try:
                # This would call the actual validation logic
                credential.validate_credentials()
                self.message_user(
                    request, 
                    f"Credentials validated for {credential.exchange.name}"
                )
            except Exception as e:
                self.message_user(
                    request, 
                    f"Validation failed for {credential.exchange.name}: {str(e)}",
                    level='ERROR'
                )
    validate_credentials.short_description = "Validate selected credentials"
    
    def enable_trading(self, request, queryset):
        """Admin action to enable trading"""
        updated = queryset.update(trading_enabled=True)
        self.message_user(
            request, 
            f"Trading enabled for {updated} credential(s)"
        )
    enable_trading.short_description = "Enable trading for selected"
    
    def disable_trading(self, request, queryset):
        """Admin action to disable trading"""
        updated = queryset.update(trading_enabled=False)
        self.message_user(
            request, 
            f"Trading disabled for {updated} credential(s)"
        )
    disable_trading.short_description = "Disable trading for selected"