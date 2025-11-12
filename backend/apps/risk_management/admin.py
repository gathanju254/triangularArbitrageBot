# backend/apps/risk_management/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    RiskConfig, RiskMetrics, TradeLimit, 
    RiskAlert, CircuitBreakerLog, RiskReport
)

@admin.register(RiskConfig)
class RiskConfigAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'risk_tolerance', 'max_position_size_usd', 
        'max_daily_loss_usd', 'max_trades_per_day', 
        'enable_circuit_breaker', 'created_at'
    )
    list_filter = (
        'risk_tolerance', 'enable_circuit_breaker', 
        'enable_trading_hours', 'created_at', 'updated_at'
    )
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'risk_tolerance')
        }),
        ('Position Sizing', {
            'fields': (
                'max_position_size_usd', 
                'max_position_percentage'
            )
        }),
        ('Loss Limits', {
            'fields': (
                'max_daily_loss_usd',
                'max_daily_loss_percentage',
                'max_drawdown_percentage'
            )
        }),
        ('Trading Limits', {
            'fields': (
                'max_trades_per_day',
                'max_concurrent_trades',
                'max_daily_volume',
                'min_profit_threshold'
            )
        }),
        ('Circuit Breakers', {
            'fields': (
                'enable_circuit_breaker',
                'circuit_breaker_threshold'
            )
        }),
        ('Risk Monitoring', {
            'fields': (
                'volatility_threshold',
                'liquidity_threshold'
            )
        }),
        ('Trading Hours', {
            'fields': (
                'enable_trading_hours',
                'trading_hours_start',
                'trading_hours_end'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(RiskMetrics)
class RiskMetricsAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date', 'daily_pnl', 'daily_trades', 
        'daily_volume', 'loss_breach_display', 
        'circuit_breaker_display'
    )
    list_filter = (
        'date', 'loss_breach', 'position_breach', 
        'volume_breach', 'circuit_breaker_triggered',
        'trading_hours_violation', 'concentration_risk'
    )
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('date',)
    list_per_page = 25
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date')
        }),
        ('Daily Trading Metrics', {
            'fields': (
                'daily_trades',
                'daily_volume',
                'daily_pnl'
            )
        }),
        ('Performance Metrics', {
            'fields': (
                'sharpe_ratio',
                'volatility',
                'max_drawdown',
                'win_rate',
                'average_profit',
                'average_loss'
            )
        }),
        ('Risk Flags', {
            'fields': (
                'loss_breach',
                'position_breach',
                'volume_breach',
                'circuit_breaker_triggered',
                'trading_hours_violation',
                'concentration_risk'
            )
        })
    )
    
    def loss_breach_display(self, obj):
        if obj.loss_breach:
            return format_html('<span style="color: red; font-weight: bold;">● BREACHED</span>')
        return format_html('<span style="color: green;">● OK</span>')
    loss_breach_display.short_description = 'Loss Breach'
    
    def circuit_breaker_display(self, obj):
        if obj.circuit_breaker_triggered:
            return format_html('<span style="color: orange; font-weight: bold;">● TRIGGERED</span>')
        return format_html('<span style="color: green;">● NORMAL</span>')
    circuit_breaker_display.short_description = 'Circuit Breaker'


@admin.register(TradeLimit)
class TradeLimitAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'limit_type_display', 'limit_value', 
        'current_value', 'breach_status', 'is_active', 
        'breached_at'
    )
    list_filter = (
        'limit_type', 'is_breached', 'is_active', 
        'breached_at', 'created_at'
    )
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'breached_at')
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'limit_type', 'is_active')
        }),
        ('Limit Values', {
            'fields': (
                'limit_value',
                'current_value'
            )
        }),
        ('Breach Status', {
            'fields': (
                'is_breached',
                'breached_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def limit_type_display(self, obj):
        return obj.get_limit_type_display()
    limit_type_display.short_description = 'Limit Type'
    
    def breach_status(self, obj):
        if obj.is_breached:
            return format_html('<span style="color: red; font-weight: bold;">● BREACHED</span>')
        return format_html('<span style="color: green;">● OK</span>')
    breach_status.short_description = 'Status'


@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'alert_type_display', 'severity_display', 
        'is_resolved', 'acknowledged', 'created_at'
    )
    list_filter = (
        'alert_type', 'severity', 'is_resolved', 
        'acknowledged', 'created_at'
    )
    search_fields = (
        'user__username', 'user__email', 'message', 
        'metric'
    )
    readonly_fields = ('created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Alert Information', {
            'fields': (
                'user',
                'alert_type',
                'severity',
                'message'
            )
        }),
        ('Metrics', {
            'fields': (
                'metric',
                'value',
                'threshold'
            )
        }),
        ('Status', {
            'fields': (
                'is_resolved',
                'resolved_at',
                'acknowledged',
                'acknowledged_at',
                'acknowledged_by'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def alert_type_display(self, obj):
        return obj.get_alert_type_display()
    alert_type_display.short_description = 'Alert Type'
    
    def severity_display(self, obj):
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_display().upper()
        )
    severity_display.short_description = 'Severity'
    
    actions = ['mark_as_resolved', 'mark_as_acknowledged']
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} alerts marked as resolved.')
    mark_as_resolved.short_description = "Mark selected alerts as resolved"
    
    def mark_as_acknowledged(self, request, queryset):
        updated = queryset.update(acknowledged=True)
        self.message_user(request, f'{updated} alerts marked as acknowledged.')
    mark_as_acknowledged.short_description = "Mark selected alerts as acknowledged"


@admin.register(CircuitBreakerLog)
class CircuitBreakerLogAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'trigger_type_display', 'is_active', 
        'activated_at', 'deactivated_at', 'duration_minutes'
    )
    list_filter = (
        'trigger_type', 'is_active', 'activated_at'
    )
    search_fields = (
        'user__username', 'user__email', 'message'
    )
    readonly_fields = ('activated_at', 'deactivated_at', 'duration_minutes')
    list_per_page = 20
    date_hierarchy = 'activated_at'
    
    fieldsets = (
        ('Circuit Breaker Information', {
            'fields': (
                'user',
                'trigger_type',
                'message'
            )
        }),
        ('Trigger Values', {
            'fields': (
                'trigger_value',
                'threshold'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'activated_at',
                'deactivated_at',
                'duration_minutes'
            )
        })
    )
    
    def trigger_type_display(self, obj):
        return obj.get_trigger_type_display()
    trigger_type_display.short_description = 'Trigger Type'


@admin.register(RiskReport)
class RiskReportAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'report_type_display', 'period_start', 
        'period_end', 'generated_at'
    )
    list_filter = (
        'report_type', 'period_start', 'period_end', 
        'generated_at'
    )
    search_fields = (
        'user__username', 'user__email', 'summary', 
        'recommendations'
    )
    readonly_fields = ('generated_at',)
    list_per_page = 20
    date_hierarchy = 'period_start'
    
    fieldsets = (
        ('Report Information', {
            'fields': (
                'user',
                'report_type',
                'period_start',
                'period_end'
            )
        }),
        ('Content', {
            'fields': (
                'summary',
                'recommendations',
                'report_data'
            )
        }),
        ('Timestamps', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        })
    )
    
    def report_type_display(self, obj):
        return obj.get_report_type_display()
    report_type_display.short_description = 'Report Type'


# Custom admin site configuration
admin.site.site_header = "Tudollar Risk Management Administration"
admin.site.site_title = "Tudollar Risk Management"
admin.site.index_title = "Risk Management Dashboard"