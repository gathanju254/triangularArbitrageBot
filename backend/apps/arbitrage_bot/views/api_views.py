# backend/apps/arbitrage_bot/views/api_views.py
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
import time
import threading
from ..core.arbitrage_engine import arbitrage_engine, ArbitrageEngine
from ..core.market_data import market_data_manager, MarketDataManager
from ..core.order_execution import OrderExecutor
from ..models.trade import TradeRecord, BotConfig
from ..models.arbitrage_opportunity import ArbitrageOpportunityRecord
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from django.db import models

logger = logging.getLogger(__name__)

# Global instances
arbitrage_engine_instance = arbitrage_engine
market_data_manager_instance = market_data_manager
order_executor = OrderExecutor()
system_running = False

# Global trading monitor state
trading_monitor_running = False
trading_monitor_thread = None

def initialize_system():
    """Initialize system components with comprehensive sample data"""
    global market_data_manager_instance, arbitrage_engine_instance
    
    logger.info("Initializing arbitrage system with sample data...")
    
    # Always use sample data for demo purposes
    market_data_manager_instance.add_sample_prices()
    
    # Get symbols from sample prices
    sample_prices = market_data_manager_instance.get_all_prices()
    symbols = list(sample_prices.keys())
    
    logger.info(f"Available symbols: {symbols}")
    
    # Initialize triangles with improved detection
    triangles_found = arbitrage_engine_instance.find_triangles(symbols)
    
    # Enhanced manual triangle fallback
    if not triangles_found:
        logger.warning("No triangles found automatically, checking manual triangles")
        manual_triangles = [
            ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'],
            ['ETH/USDT', 'ADA/ETH', 'ADA/USDT'], 
            ['BTC/USDT', 'BNB/BTC', 'BNB/USDT'],
            ['ETH/USDT', 'DOT/ETH', 'DOT/USDT'],
            ['BTC/USDT', 'LINK/BTC', 'LINK/USDT'],
        ]
        
        # Filter to only include triangles where all pairs exist in sample data
        triangles_found = []
        for triangle in manual_triangles:
            if all(pair in symbols for pair in triangle):
                triangles_found.append(triangle)
                logger.info(f"✅ Added manual triangle: {triangle}")
            else:
                missing = [pair for pair in triangle if pair not in symbols]
                logger.warning(f"❌ Skipping triangle {triangle} - missing pairs: {missing}")
        
        arbitrage_engine_instance.triangles = triangles_found
    
    # Log initialization details
    logger.info(f"System initialization complete:")
    logger.info(f"   - {len(sample_prices)} sample prices loaded") 
    logger.info(f"   - {len(triangles_found)} triangular paths configured")
    logger.info(f"   - Minimum profit threshold: {arbitrage_engine_instance.min_profit_threshold}%")
    
    # Scan for initial opportunities with sample data
    price_values = {}
    for symbol, price_data in sample_prices.items():
        if isinstance(price_data, dict) and 'price' in price_data:
            price_values[symbol] = price_data['price']
        else:
            price_values[symbol] = price_data
    
    initial_opportunities = arbitrage_engine_instance.scan_opportunities(price_values)
    logger.info(f"   - {len(initial_opportunities)} initial opportunities found")
    
    # Log some opportunity details
    for i, opp in enumerate(initial_opportunities[:3]):
        logger.info(f"     Opportunity {i+1}: {opp.triangle} - {opp.profit_percentage:.4f}%")

# Call initialization when module loads
initialize_system()

@api_view(['GET'])
def get_opportunities(request):
    """Get current arbitrage opportunities (persist top opportunities to DB)"""
    try:
        demo_exchange = request.query_params.get('demo')
        if demo_exchange:
            market_data_manager_instance.add_demo_prices(demo_exchange)
            logger.info(f"Using demo prices for: {demo_exchange}")

        current_prices = market_data_manager_instance.get_all_prices()
        price_values = {}
        for symbol, price_data in current_prices.items():
            if isinstance(price_data, dict) and 'price' in price_data:
                price_values[symbol] = price_data['price']
            else:
                price_values[symbol] = price_data

        # Fallback to sample initialization if no prices
        if not price_values:
            initialize_system()
            current_prices = market_data_manager_instance.get_all_prices()
            for symbol, price_data in current_prices.items():
                if isinstance(price_data, dict) and 'price' in price_data:
                    price_values[symbol] = price_data['price']
                else:
                    price_values[symbol] = price_data

        opportunities = arbitrage_engine_instance.scan_opportunities(price_values)

        serialized_opportunities = []
        for opp in opportunities:
            # Normalize profit percentage to a numeric percent value.
            try:
                raw_pct = getattr(opp, "profit_percentage", 0.0)
                p = float(raw_pct or 0.0)
            except Exception:
                # defensive fallback
                try:
                    p = float(opp.profit if hasattr(opp, 'profit') else 0.0)
                except Exception:
                    p = 0.0

            # --- ADDED LOGGING FOR PROFIT CALC ---
            try:
                cfg, _ = BotConfig.objects.get_or_create(pk=1)
                min_profit_threshold = float(getattr(cfg, "min_profit_threshold", 0.3))
            except Exception:
                min_profit_threshold = 0.3

            fee_estimate = 0.2  # percent assumed
            p_pct = float(p)
            effective_profit = round(p_pct - fee_estimate, 6)
            logger.info(f"Profit calc: {p_pct:.6f}% - {fee_estimate:.2f}% fees = {effective_profit:.6f}% (threshold: {min_profit_threshold:.2f}%)")
            # --- END ADDED LOGGING ---

            # If caller returned a fractional value (e.g. 0.0034 meaning 0.34%), convert to percent.
            if 0 < abs(p) < 0.01:
                p = p * 100.0

            p = round(p, 4)

            serialized = {
                'triangle': opp.triangle,
                'profit_percentage': p,
                'timestamp': opp.timestamp.isoformat() if hasattr(opp.timestamp, 'isoformat') else str(opp.timestamp),
                'prices': {pair: round(price, 6) for pair, price in opp.prices.items()},
                'steps': getattr(opp, 'steps', [])
            }
            serialized_opportunities.append(serialized)

        # Persist top N opportunities to DB (non-blocking)
        try:
            to_create = []
            source = 'demo' if demo_exchange else 'live'
            for sopp in serialized_opportunities[:10]:
                to_create.append(ArbitrageOpportunityRecord(
                    triangle=sopp['triangle'],
                    profit_percentage=float(sopp['profit_percentage']),
                    prices=sopp['prices'],
                    steps=sopp.get('steps', []),
                    source=source
                ))
            if to_create:
                ArbitrageOpportunityRecord.objects.bulk_create(to_create)
        except Exception as e:
            logger.warning(f"Could not persist opportunities: {e}")

        market_stats = market_data_manager_instance.get_price_statistics()
        engine_stats = arbitrage_engine_instance.get_triangle_statistics()

        return Response({
            'opportunities': serialized_opportunities,
            'count': len(serialized_opportunities),
            'market_data': market_stats,
            'engine_status': engine_stats,
            'system_status': 'running' if system_running else 'stopped'
        })

    except Exception as e:
        logger.error(f"Error fetching opportunities: {e}")
        
        # Enhanced fallback to sample data with realistic opportunities
        sample_opportunities = [
            {
                'triangle': ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'],
                'profit_percentage': 0.45,
                'timestamp': '2024-01-01T12:00:00',
                'prices': {'BTC/USDT': 45000.0, 'ETH/BTC': 0.06, 'ETH/USDT': 2700.0},
                'steps': ['1.0000 BTC -> 45000.0000 USDT', '45000.0000 USDT -> 16.6667 ETH', '16.6667 ETH -> 1.0045 BTC']
            },
            {
                'triangle': ['ETH/USDT', 'ADA/ETH', 'ADA/USDT'],
                'profit_percentage': 0.32,
                'timestamp': '2024-01-01T12:00:00',
                'prices': {'ETH/USDT': 2700.0, 'ADA/ETH': 0.0002, 'ADA/USDT': 0.55},
                'steps': ['1.0000 ETH -> 2700.0000 USDT', '2700.0000 USDT -> 4909.0909 ADA', '4909.0909 ADA -> 1.0032 ETH']
            },
            {
                'triangle': ['BNB/USDT', 'BTC/BNB', 'USDT/BTC'],
                'profit_percentage': 0.28,
                'timestamp': '2024-01-01T12:00:00',
                'prices': {'BNB/USDT': 320.0, 'BTC/BNB': 0.003125, 'USDT/BTC': 0.000022},
                'steps': ['1.0000 BNB -> 320.0000 USDT', '320.0000 USDT -> 0.0070 BTC', '0.0070 BTC -> 1.0028 BNB']
            }
        ]
        
        return Response({
            'opportunities': sample_opportunities,
            'count': len(sample_opportunities),
            'note': 'Using sample data - arbitrage engine encountered an error',
            'error': str(e),
            'system_status': 'stopped'
        })

@api_view(['GET'])
def get_performance(request):
    """Get performance and profit history data"""
    try:
        days = int(request.query_params.get('days', 7))
        
        # Generate mock profit history (replace with real data from your database)
        import random
        from datetime import datetime, timedelta
        
        profit_history = []
        base_profit = 100
        for i in range(days, 0, -1):
            date = datetime.now() - timedelta(days=i)
            profit = base_profit + (random.random() * 50 - 25)
            base_profit = profit
            
            profit_history.append({
                'date': date.strftime('%Y-%m-%d'),
                'profit': max(0, float(profit)),
                'cumulative': float(base_profit)
            })
        
        # Mock stats
        stats = {
            'total_profit': 1250.75,
            'total_trades': 45,
            'success_rate': 87.5,
            'active_opportunities': 3,
            'today_profit': 150.25,
            'avg_profit_percentage': 2.5,
            'total_opportunities': 156,
            'successful_trades': 39,
            'avg_profit_per_trade': 27.53
        }
        
        return Response({
            'profit_history': profit_history,
            'stats': stats,
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting performance data: {e}")
        return Response({
            'error': 'Failed to get performance data',
            'profit_history': [],
            'stats': {}
        }, status=500)

@api_view(['GET'])
def system_status(request):
    """Get current system status"""
    try:
        # Get current prices for opportunity scanning
        current_prices = market_data_manager_instance.get_all_prices()
        price_values = {}
        for symbol, price_data in current_prices.items():
            if isinstance(price_data, dict) and 'price' in price_data:
                price_values[symbol] = price_data['price']
            else:
                price_values[symbol] = price_data
        
        opportunities = arbitrage_engine_instance.scan_opportunities(price_values)
        opportunities_count = len(opportunities)
        
    except Exception as e:
        logger.error(f"Error scanning opportunities for status: {e}")
        opportunities_count = 0
    
    # Get connection status and statistics
    connection_status = market_data_manager_instance.get_connection_status()
    market_stats = market_data_manager_instance.get_price_statistics()
    engine_stats = arbitrage_engine_instance.get_triangle_statistics()
    
    # Check if we're using sample data
    using_sample_data = market_stats.get('websocket_available', False) and not any(connection_status.values())
    
    # Calculate system health score
    health_score = 100
    if not market_stats['recent_symbols']:
        health_score -= 30
    if not engine_stats['total_triangles']:
        health_score -= 20
    if not any(connection_status.values()):
        health_score -= 10
    
    return Response({
        'status': 'running' if system_running else 'stopped',
        'opportunities_count': opportunities_count,
        'market_data_connected': market_data_manager_instance.is_connected,
        'connections': connection_status,
        'market_stats': market_stats,
        'engine_stats': engine_stats,
        'health_score': max(0, health_score),
        'using_sample_data': using_sample_data,
        'timestamp': time.time()
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
            market_data_manager_instance.start_all_websockets()
            
            # Check if WebSocket actually connected
            connection_status = market_data_manager_instance.get_connection_status()
            any_connected = any(connection_status.values())
            
            if not any_connected:
                logger.warning("WebSocket connections failed, using sample data")
                market_data_manager_instance.add_sample_prices()
                
            logger.info("✅ System started - WebSocket connections initiated")
            
            return Response({
                'status': 'running',
                'message': 'System started successfully',
                'connections': connection_status,
                'using_sample_data': not any_connected,
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to start system: {e}")
            system_running = False
            # Fall back to sample data
            market_data_manager_instance.add_sample_prices()
            return Response({
                'status': 'running_with_sample',
                'message': f'System started with sample data (WebSocket failed: {str(e)})',
                'connections': market_data_manager_instance.get_connection_status(),
                'using_sample_data': True,
                'timestamp': time.time()
            })
            
    elif action == 'stop':
        system_running = False
        # Stop market data collection
        try:
            market_data_manager_instance.stop_websocket()
            logger.info("🛑 System stopped - WebSocket connections closed")
            
            return Response({
                'status': 'stopped',
                'message': 'System stopped successfully',
                'connections': market_data_manager_instance.get_connection_status(),
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"⚠️ Error stopping websocket: {e}")
            # Still return success as we're stopping the system
            return Response({
                'status': 'stopped',
                'message': 'System stopped (with some cleanup errors)',
                'warning': f'Cleanup errors: {str(e)}',
                'connections': market_data_manager_instance.get_connection_status(),
                'timestamp': time.time()
            })
    
    else:
        return Response({
            'status': 'error',
            'message': 'Invalid action. Use "start" or "stop"',
            'timestamp': time.time()
        }, status=400)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        # Test all components
        market_stats = market_data_manager_instance.get_price_statistics()
        engine_stats = arbitrage_engine_instance.get_triangle_statistics()
        connection_status = market_data_manager_instance.get_connection_status()
        
        components = {
            'arbitrage_engine': 'operational',
            'market_data': 'operational',
            'order_executor': 'operational' if order_executor else 'unknown',
            'web_server': 'operational'
        }
        
        # Check if components have data
        if market_stats['total_symbols'] == 0:
            components['market_data'] = 'no_data'
        if engine_stats['total_triangles'] == 0:
            components['arbitrage_engine'] = 'no_triangles'
        
        # Calculate overall health
        health_score = 100
        if components['market_data'] != 'operational':
            health_score -= 30
        if components['arbitrage_engine'] != 'operational':
            health_score -= 30
        
        # Check if using sample data
        using_sample_data = market_stats.get('websocket_available', False) and not any(connection_status.values())
        
        return Response({
            'status': 'healthy' if health_score >= 80 else 'degraded',
            'system_running': system_running,
            'components': components,
            'market_stats': market_stats,
            'engine_stats': engine_stats,
            'connections': connection_status,
            'health_score': health_score,
            'using_sample_data': using_sample_data,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return Response({
            'status': 'unhealthy',
            'system_running': system_running,
            'error': str(e),
            'components': {
                'arbitrage_engine': 'error',
                'market_data': 'error',
                'order_executor': 'unknown',
                'web_server': 'operational'
            },
            'timestamp': time.time()
        }, status=500)

@api_view(['POST'])
@csrf_exempt
def reset_system(request):
    """Reset system and reinitialize"""
    try:
        global system_running
        
        # Stop the system first
        system_running = False
        market_data_manager_instance.stop_websocket()
        
        # Clear existing data
        market_data_manager_instance.prices = {}
        arbitrage_engine_instance.clear_triangles()
        
        # Reinitialize
        initialize_system()
        
        logger.info("🔄 System reset and reinitialized")
        
        return Response({
            'message': 'System reset successfully',
            'status': 'stopped',
            'initialized': True,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ System reset failed: {e}")
        return Response({
            'error': f'System reset failed: {str(e)}',
            'timestamp': time.time()
        }, status=500)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def trading_config(request):
    """Get or update trading configuration"""
    try:
        if request.method == 'GET':
            # Get or create bot config
            config, created = BotConfig.objects.get_or_create(pk=1)
            
            return Response({
                'auto_trading': config.trading_enabled,
                'trading_mode': 'full-auto' if config.trading_enabled else 'manual',
                'max_concurrent_trades': config.max_concurrent_trades or 3,
                'min_trade_amount': config.min_trade_amount or 10.0,
                'stop_loss_enabled': True,  # Default values
                'take_profit_enabled': True,
                'stop_loss_percent': 2.0,
                'take_profit_percent': 5.0,
                'email_notifications': True,
                'push_notifications': False,
                'trading_alerts': True,
                'risk_alerts': True,
                'slippage_tolerance': config.slippage_tolerance or 0.1,
                'enabled_exchanges': config.enabled_exchanges_list,
            })
            
        elif request.method == 'PUT':
            data = request.data
            config, created = BotConfig.objects.get_or_create(pk=1)
            
            # Update config with form data
            if 'auto_trading' in data:
                config.trading_enabled = data['auto_trading']
            if 'min_trade_amount' in data:
                config.min_trade_amount = float(data['min_trade_amount'])
            if 'max_concurrent_trades' in data:
                config.max_concurrent_trades = int(data['max_concurrent_trades'])
            if 'slippage_tolerance' in data:
                config.slippage_tolerance = float(data['slippage_tolerance'])
            
            config.save()
            
            return Response({
                'message': 'Trading configuration updated successfully',
                'config': {
                    'auto_trading': config.trading_enabled,
                    'min_trade_amount': config.min_trade_amount,
                    'max_concurrent_trades': config.max_concurrent_trades,
                    'slippage_tolerance': config.slippage_tolerance,
                }
            })
            
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=400)