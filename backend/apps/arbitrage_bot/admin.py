from django.contrib import admin
from .models.trade import TradeRecord, BotConfig
from .models.arbitrage_opportunity import ArbitrageOpportunityRecord

@admin.register(TradeRecord)
class TradeRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'exchange', 'profit', 'profit_percentage', 'entry_amount', 'exit_amount', 'status', 'timestamp')
    list_filter = ('exchange', 'status')
    search_fields = ('triangle', 'exchange')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

@admin.register(ArbitrageOpportunityRecord)
class ArbitrageOpportunityAdmin(admin.ModelAdmin):
    list_display = ('id', 'profit_percentage', 'source', 'timestamp')
    list_filter = ('source',)
    search_fields = ('triangle',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

@admin.register(BotConfig)
class BotConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'base_balance', 'max_position_size', 'max_daily_loss', 'min_profit_threshold')
    readonly_fields = ()
