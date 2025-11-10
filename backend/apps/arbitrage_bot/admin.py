# backend/apps/arbitrage_bot/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime

# Import models from arbitrage_bot app only
from .models.trade import TradeRecord
from .models.arbitrage_opportunity import ArbitrageOpportunityRecord
from .models.risk_alert import RiskAlert

# REMOVED: BotConfiguration import and registration from this file


@admin.register(TradeRecord)
class TradeRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'exchange',
        'status',
        'profit_display',
        'profit_percentage_display',
        'entry_amount',
        'exit_amount',
        'triangle_display',
        'timestamp',
    )
    list_filter = ('exchange', 'status')
    search_fields = ('triangle', 'exchange', 'status')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    list_select_related = False

    def triangle_display(self, obj):
        try:
            tri = obj.triangle or []
            if isinstance(tri, (list, tuple)):
                return " → ".join(tri)
            return str(tri)
        except Exception:
            return str(obj.triangle)
    triangle_display.short_description = 'Triangle'

    def profit_display(self, obj):
        return f"${float(obj.profit):+.4f}"
    profit_display.short_description = 'Profit'
    profit_display.admin_order_field = 'profit'

    def profit_percentage_display(self, obj):
        return f"{float(obj.profit_percentage):.4f}%"
    profit_percentage_display.short_description = 'Profit %'
    profit_percentage_display.admin_order_field = 'profit_percentage'


@admin.register(ArbitrageOpportunityRecord)
class ArbitrageOpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source',
        'profit_percentage_display',
        'triangle_display',
        'timestamp',
    )
    list_filter = ('source',)
    search_fields = ('triangle',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

    def triangle_display(self, obj):
        try:
            tri = obj.triangle or []
            if isinstance(tri, (list, tuple)):
                return " → ".join(tri)
            return str(tri)
        except Exception:
            return str(obj.triangle)
    triangle_display.short_description = 'Triangle'

    def profit_percentage_display(self, obj):
        return f"{float(obj.profit_percentage):.4f}%"
    profit_percentage_display.short_description = 'Profit %'
    profit_percentage_display.admin_order_field = 'profit_percentage'


@admin.register(RiskAlert)
class RiskAlertAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_display',
        'alert_type',
        'severity',
        'metric',
        'value',
        'threshold',
        'is_resolved',
        'created_at',
        'resolved_at',
    )
    list_filter = ('severity', 'is_resolved')
    search_fields = ('alert_type', 'message', 'metric', 'user__username')
    readonly_fields = ('created_at', 'resolved_at')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': (
                'user',
                'alert_type',
                'severity',
                'message',
            )
        }),
        ('Metric & Threshold', {
            'fields': (
                'metric',
                'value',
                'threshold',
            )
        }),
        ('Status', {
            'fields': (
                'is_resolved',
                'resolved_at',
                'created_at',
            )
        }),
    )

    def user_display(self, obj):
        try:
            return obj.user.username
        except Exception:
            return str(obj.user)
    user_display.short_description = 'User'