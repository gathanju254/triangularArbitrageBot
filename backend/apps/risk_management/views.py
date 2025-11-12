# backend/apps/risk_management/views.py
from decimal import Decimal
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import RiskConfig, RiskMetrics, TradeLimit
from .serializers import (
    RiskConfigSerializer, 
    RiskMetricsSerializer, 
    TradeLimitSerializer,
    RiskOverviewSerializer
)
from .services import RiskManagementService

class RiskConfigViewSet(viewsets.ModelViewSet):
    serializer_class = RiskConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RiskConfig.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RiskMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RiskMetricsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RiskMetrics.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current day's risk metrics"""
        today = timezone.now().date()
        metrics = RiskMetrics.objects.filter(user=request.user, date=today).first()
        
        if metrics:
            serializer = self.get_serializer(metrics)
            return Response(serializer.data)
        return Response({})

# Add the missing RiskMetricsView for direct API access
class RiskMetricsView(generics.ListAPIView):
    serializer_class = RiskMetricsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RiskMetrics.objects.filter(user=self.request.user)

class TradeLimitViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradeLimitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TradeLimit.objects.filter(user=self.request.user)

class RiskOverviewView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RiskOverviewSerializer

    def get_object(self):
        user = self.request.user
        overview_data = RiskManagementService.get_user_risk_overview(user)
        
        # Convert to serializer-compatible format
        return {
            'total_pnl': overview_data.get('total_pnl', Decimal('0.0')),
            'daily_pnl': overview_data.get('daily_pnl', Decimal('0.0')),
            'active_limits': overview_data.get('active_limits', 0),
            'breached_limits': overview_data.get('breached_limits', 0),
            'risk_score': overview_data.get('risk_score', 0.0)
        }

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_trade_compliance(request):
    """Check if trade complies with risk limits"""
    trade_data = request.data
    is_compliant, message = RiskManagementService.check_trade_compliance(
        request.user, trade_data
    )
    
    return Response({
        'is_compliant': is_compliant,
        'message': message
    })

# Helper functions (you'll need to implement these based on your trading data)
def calculate_total_pnl(user):
    # Implementation for total PnL calculation
    # This should query your trading history
    return Decimal('0.0')

def calculate_daily_pnl(user):
    # Implementation for daily PnL calculation
    today = timezone.now().date()
    try:
        metrics = RiskMetrics.objects.get(user=user, date=today)
        return metrics.daily_pnl
    except RiskMetrics.DoesNotExist:
        return Decimal('0.0')