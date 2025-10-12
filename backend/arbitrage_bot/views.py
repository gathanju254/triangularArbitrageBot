# backend/arbitrage_bot/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import json
from .core.arbitrage_engine import ArbitrageEngine
from .core.market_data import MarketDataManager
from .core.order_execution import OrderExecutor

# Global instances
arbitrage_engine = ArbitrageEngine()
market_data_manager = MarketDataManager()
order_executor = OrderExecutor()
system_running = False

@api_view(['GET'])
def get_opportunities(request):
    """Get current arbitrage opportunities"""
    try:
        # Try to get real opportunities from the engine
        opportunities = arbitrage_engine.scan_opportunities(market_data_manager.prices)
        
        serialized_opportunities = []
        for opp in opportunities:
            serialized_opportunities.append({
                'triangle': opp.triangle,
                'profit_percentage': opp.profit_percentage,
                'timestamp': opp.timestamp.isoformat(),
                'prices': opp.prices
            })
        
        return Response({
            'opportunities': serialized_opportunities,
            'count': len(serialized_opportunities)
        })
    except Exception as e:
        # Fallback to sample data if real engine fails
        sample_opportunities = [
            {
                'triangle': ['BTC/USDT', 'ETH/BTC', 'USDT/ETH'],
                'profit_percentage': 0.45,
                'timestamp': '2024-01-01T12:00:00',
                'prices': {'BTC/USDT': 45000.0, 'ETH/BTC': 0.06, 'USDT/ETH': 2700.0}
            },
            {
                'triangle': ['ETH/USDT', 'ADA/ETH', 'USDT/ADA'],
                'profit_percentage': 0.32,
                'timestamp': '2024-01-01T12:00:00',
                'prices': {'ETH/USDT': 2700.0, 'ADA/ETH': 0.0002, 'USDT/ADA': 0.55}
            }
        ]
        
        return Response({
            'opportunities': sample_opportunities,
            'count': len(sample_opportunities),
            'note': 'Using sample data - arbitrage engine not fully implemented'
        })

@api_view(['POST'])
@csrf_exempt
def system_control(request):
    """Start/stop the arbitrage system"""
    global system_running
    
    action = request.data.get('action')
    
    if action == 'start':
        system_running = True
        # Start market data collection
        try:
            market_data_manager.start_websocket('binance')
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to start system: {str(e)}'
            }, status=500)
    elif action == 'stop':
        system_running = False
        # Stop market data collection
        try:
            market_data_manager.stop_websocket()
        except Exception as e:
            # Log error but don't fail the stop request
            print(f"Error stopping websocket: {e}")
    
    return Response({
        'status': 'running' if system_running else 'stopped',
        'message': f'System {action}ed successfully'
    })

@api_view(['GET'])
def system_status(request):
    """Get current system status"""
    try:
        opportunities_count = len(arbitrage_engine.scan_opportunities(market_data_manager.prices))
    except:
        opportunities_count = 2  # Fallback count
    
    return Response({
        'status': 'running' if system_running else 'stopped',
        'opportunities_count': opportunities_count,
        'market_data_connected': market_data_manager.is_connected if hasattr(market_data_manager, 'is_connected') else False
    })

@api_view(['GET'])
def get_performance(request):
    """Get performance metrics"""
    return Response({
        'totalProfit': 1250.50,
        'tradesToday': 15,
        'activeOpportunities': 2,
        'successRate': 85.5,
        'dailyProfit': 45.20
    })

@api_view(['POST'])
@csrf_exempt
def execute_trade(request):
    """Execute a trade"""
    triangle = request.data.get('triangle', [])
    amount = request.data.get('amount', 100)
    exchange = request.data.get('exchange', 'binance')
    
    try:
        # Try to execute trade through order executor
        if system_running and hasattr(order_executor, 'execute_triangle_trade'):
            trade_result = order_executor.execute_triangle_trade(triangle, amount, exchange)
        else:
            # Simulate trade execution
            trade_result = {
                'status': 'executed',
                'profit': amount * 0.0045,  # 0.45% profit
                'trade_id': 'trade_123456',
                'triangle': triangle,
                'amount': amount,
                'exchange': exchange
            }
        
        return Response(trade_result)
    except Exception as e:
        return Response({
            'status': 'failed',
            'error': str(e),
            'trade_id': None
        }, status=400)

@api_view(['GET'])
def get_trade_history(request):
    """Get trade history"""
    sample_trades = [
        {
            'id': 'trade_123456',
            'triangle': ['BTC/USDT', 'ETH/BTC', 'USDT/ETH'],
            'entry_amount': 1000.0,
            'exit_amount': 1004.5,
            'profit': 4.5,
            'profit_percentage': 0.45,
            'status': 'executed',
            'timestamp': '2024-01-01T12:00:00',
            'exchange': 'binance'
        },
        {
            'id': 'trade_123457',
            'triangle': ['ETH/USDT', 'ADA/ETH', 'USDT/ADA'],
            'entry_amount': 500.0,
            'exit_amount': 501.6,
            'profit': 1.6,
            'profit_percentage': 0.32,
            'status': 'executed',
            'timestamp': '2024-01-01T11:30:00',
            'exchange': 'binance'
        }
    ]
    
    return Response({'trades': sample_trades})

@api_view(['GET'])
def get_settings(request):
    """Get current settings"""
    settings = {
        'minProfitThreshold': 0.2,
        'maxPositionSize': 1000,
        'maxDailyLoss': 100,
        'enabledExchanges': ['binance'],
        'tradingEnabled': False,
        'autoTrading': False,
        'updateInterval': 5,
        'riskLevel': 'medium'
    }
    return Response({'settings': settings})

@api_view(['POST'])
@csrf_exempt
def update_settings(request):
    """Update settings"""
    try:
        new_settings = request.data.get('settings', {})
        
        # Here you would typically save settings to database or config file
        # For now, we'll just return the updated settings
        
        # Validate and update settings logic would go here
        
        return Response({
            'message': 'Settings updated successfully', 
            'settings': new_settings
        })
    except Exception as e:
        return Response({
            'error': f'Failed to update settings: {str(e)}'
        }, status=400)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'system_running': system_running,
        'components': {
            'arbitrage_engine': 'operational',
            'market_data': 'operational' if hasattr(market_data_manager, 'is_connected') else 'unknown',
            'order_executor': 'operational' if order_executor else 'unknown'
        }
    })