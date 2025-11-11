# backend/apps/trading/views/__init__.py
# backend/apps/trading/views/__init__.py

from .api_views import *
from .web_views import *
from .admin_views import *

__all__ = [
    # API Views
    'TradingConfigViewSet',
    'OrderViewSet', 
    'TradingDashboardViewSet',
    'ManualTradingViewSet',
    'IntegratedRiskDashboardViewSet',
    
    # Web Views
    'TradingDashboardView',
    
    # APIView classes
    'ArbitrageOpportunityView',
    'ExecuteTradeView',
    'AutoTradingStatusView',
    'TradingEngineControlView',
    'ExecuteArbitrageTradeView',
    'ExecuteSequentialArbitrageView',
    'ValidateArbitrageOpportunityView',
    'ScanArbitrageOpportunitiesView',
    'ArbitrageAnalyticsView',
    'ArbitrageTradeHistoryView',
    'RiskCheckView',
    'RiskComplianceView',
    'RiskOverviewView',
    'RiskLimitsView',
    'RiskAlertsView',
    'RiskConfigView',
    'RiskMetricsView',
    'IntegratedTradeExecutionView',
    'IntegratedTradingDashboardView',
    'IntegratedAnalyticsView',
    'IntegratedSystemStatusView',
    'IntegratedRiskDashboardView',
]