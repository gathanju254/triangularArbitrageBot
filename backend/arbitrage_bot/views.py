# backend/arbitrage_bot/views.py
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging
import time
import threading
from .core.arbitrage_engine import arbitrage_engine, ArbitrageEngine
from .core.market_data import market_data_manager, MarketDataManager
from .core.order_execution import OrderExecutor
from .models.trade import TradeRecord, BotConfig
from .models.arbitrage_opportunity import ArbitrageOpportunityRecord
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

class TradingMonitorThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        # defaults will be updated from DB
        self.profit_threshold = 0.3
        self.trade_amount = 10
        self.check_interval = 5

    def run(self):
        """Main trading monitor loop"""
        global trading_monitor_running

        logger.info("🚀 Trading monitor thread started")
        trading_monitor_running = True

        while self.running:
            try:
                # Update settings from database
                self.update_settings()

                # Get current prices
                current_prices = market_data_manager_instance.get_all_prices()
                price_values = {}
                for symbol, price_data in current_prices.items():
                    if isinstance(price_data, dict) and 'price' in price_data:
                        price_values[symbol] = price_data['price']
                    else:
                        price_values[symbol] = price_data

                opportunities = arbitrage_engine_instance.scan_opportunities(price_values)

                if opportunities:
                    best_opp = opportunities[0]
                    profit_pct = getattr(best_opp, "profit_percentage", 0.0)

                    # Auto-execute if profit exceeds threshold
                    if profit_pct > self.profit_threshold:
                        logger.info(f"Auto-executing trade with {profit_pct:.4f}% profit (threshold {self.profit_threshold}%)")

                        # Execute trade through order executor
                        try:
                            trade_result = order_executor.execute_triangle_trade(
                                best_opp.triangle,
                                self.trade_amount,
                                'binance'
                            )
                        except Exception as e:
                            logger.error(f"Auto-trade execution error: {e}")
                            trade_result = {'status': 'failed', 'error': str(e)}

                        if trade_result.get('status') == 'executed':
                            logger.info(f"✅ Auto-trade executed: ${float(trade_result.get('profit', 0)):.4f} profit")
                        else:
                            logger.warning(f"❌ Auto-trade failed: {trade_result.get('error', 'Unknown error')}")

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in trading monitor: {e}")
                time.sleep(10)  # longer delay on error

        trading_monitor_running = False
        logger.info("🛑 Trading monitor thread stopped")

    def update_settings(self):
        """Update settings from database"""
        try:
            cfg, _ = BotConfig.objects.get_or_create(pk=1)
            # use DB config values (fall back to current values)
            self.profit_threshold = float(getattr(cfg, 'min_profit_threshold', self.profit_threshold))
            # Use trade_size_fraction from config, fallback to 0.01 (1%)
            trade_size_fraction = float(getattr(cfg, 'trade_size_fraction', 0.01))
            self.trade_amount = float(getattr(cfg, 'base_balance', self.trade_amount)) * trade_size_fraction if getattr(cfg, 'base_balance', None) else self.trade_amount

            # Update risk manager settings
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.max_position_size = float(getattr(cfg, 'max_position_size', order_executor.risk_manager.max_position_size))
                order_executor.risk_manager.max_daily_loss = float(getattr(cfg, 'max_daily_loss', order_executor.risk_manager.max_daily_loss))
                order_executor.risk_manager.max_drawdown = float(getattr(cfg, 'max_drawdown', order_executor.risk_manager.max_drawdown))

        except Exception as e:
            logger.warning(f"Could not update trading monitor settings: {e}")

    def stop(self):
        """Stop the trading monitor"""
        self.running = False

@api_view(['POST'])
@csrf_exempt
def start_trading_monitor(request):
    """Start the automated trading monitor"""
    global trading_monitor_running, trading_monitor_thread

    try:
        if trading_monitor_running:
            return Response({
                'status': 'error',
                'message': 'Trading monitor is already running',
                'timestamp': time.time()
            }, status=400)

        trading_monitor_thread = TradingMonitorThread()
        trading_monitor_thread.start()
        trading_monitor_running = True

        logger.info("✅ Trading monitor started")

        return Response({
            'status': 'success',
            'message': 'Trading monitor started successfully',
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Failed to start trading monitor: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to start trading monitor: {str(e)}',
            'timestamp': time.time()
        }, status=500)

@api_view(['POST'])
@csrf_exempt
def stop_trading_monitor(request):
    """Stop the automated trading monitor"""
    global trading_monitor_running, trading_monitor_thread

    try:
        if not trading_monitor_running or not trading_monitor_thread:
            return Response({
                'status': 'error',
                'message': 'Trading monitor is not running',
                'timestamp': time.time()
            }, status=400)

        trading_monitor_thread.stop()
        trading_monitor_thread.join(timeout=10)
        trading_monitor_running = False
        trading_monitor_thread = None

        logger.info("🛑 Trading monitor stopped")

        return Response({
            'status': 'success',
            'message': 'Trading monitor stopped successfully',
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Failed to stop trading monitor: {e}")
        return Response({
            'status': 'error',
            'message': f'Failed to stop trading monitor: {str(e)}',
            'timestamp': time.time()
        }, status=500)

@api_view(['GET'])
def get_trading_monitor_status(request):
    """Get trading monitor status"""
    global trading_monitor_running

    return Response({
        'running': trading_monitor_running,
        'timestamp': time.time()
    })

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

@api_view(['GET'])
def get_performance(request):
    """Get performance metrics (real data from RiskManager + DB)"""
    try:
        # runtime components / models
        market_stats = market_data_manager_instance.get_price_statistics()
        engine_stats = arbitrage_engine_instance.get_triangle_statistics()

        # risk manager metrics
        rm = getattr(order_executor, 'risk_manager', None)
        risk_metrics = rm.get_risk_metrics() if (rm and callable(getattr(rm, 'get_risk_metrics', None))) else {}

        # execution stats
        exec_stats = getattr(order_executor, 'get_execution_stats', lambda: {})()

        # derive time-windowed stats from DB
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        total_profit_db = 0.0
        trades_today = 0
        weekly_profit = 0.0
        try:
            trades_qs = TradeRecord.objects.all()
            total_profit_db = float(trades_qs.aggregate(total=models.Sum('profit'))['total'] or 0.0)
            trades_today = trades_qs.filter(timestamp__gte=today_start).count()
            weekly_profit = float(trades_qs.filter(timestamp__gte=week_start).aggregate(total=models.Sum('profit'))['total'] or 0.0)
        except Exception as e:
            logger.debug(f"No DB trade stats available: {e}")

        # active opportunities (quick scan)
        try:
            current_prices = market_data_manager_instance.get_all_prices()
            price_values = {}
            for symbol, price_data in current_prices.items():
                if isinstance(price_data, dict) and 'price' in price_data:
                    price_values[symbol] = price_data['price']
                else:
                    price_values[symbol] = price_data
            active_opps = arbitrage_engine_instance.scan_opportunities(price_values)
            active_count = len(active_opps)
        except Exception:
            active_count = 0

        response = {
            'totalProfit': round(total_profit_db, 2),
            'tradesToday': trades_today,
            'activeOpportunities': active_count,
            'successRate': risk_metrics.get('success_rate', exec_stats.get('success_rate', 0.0)),
            'dailyProfit': round(risk_metrics.get('daily_pnl', 0.0), 2),
            'weeklyProfit': round(weekly_profit, 2),
            'monthlyProfit': round(total_profit_db, 2),
            'market_coverage': market_stats.get('total_symbols', 0),
            'triangle_efficiency': min(100, (engine_stats.get('total_triangles', 0) / max(1, market_stats.get('total_symbols', 1))) * 100),
            'risk_metrics': risk_metrics,
            'execution_stats': exec_stats,
            'timestamp': time.time()
        }

        return Response(response)

    except Exception as e:
        logger.error(f"Error generating performance metrics: {e}")
        return Response({
            'totalProfit': 0.0,
            'tradesToday': 0,
            'activeOpportunities': 0,
            'successRate': 0.0,
            'dailyProfit': 0.0,
            'weeklyProfit': 0.0,
            'monthlyProfit': 0.0,
            'market_coverage': 0,
            'triangle_efficiency': 0,
            'note': 'Using fallback performance data',
            'timestamp': time.time()
        })

@api_view(['POST'])
@csrf_exempt
def execute_trade(request):
    """Execute a trade"""
    triangle = request.data.get('triangle', [])
    amount = request.data.get('amount', 100)
    exchange = request.data.get('exchange', 'binance')
    
    try:
        # Validate the triangle first
        current_prices = market_data_manager_instance.get_all_prices()
        price_values = {}
        for symbol, price_data in current_prices.items():
            if isinstance(price_data, dict) and 'price' in price_data:
                price_values[symbol] = price_data['price']
            else:
                price_values[symbol] = price_data
        
        is_valid, validation_msg = arbitrage_engine_instance.validate_triangle(triangle, price_values)
        
        if not is_valid:
            return Response({
                'status': 'failed',
                'error': f'Invalid triangle: {validation_msg}',
                'trade_id': None,
                'timestamp': time.time()
            }, status=400)
        
        # Try to execute trade through order executor
        if system_running and hasattr(order_executor, 'execute_triangle_trade'):
            trade_result = order_executor.execute_triangle_trade(triangle, amount, exchange)
        else:
            # Simulate trade execution with realistic profit calculation
            opportunity = arbitrage_engine_instance.calculate_arbitrage(price_values, triangle)
            if opportunity:
                simulated_profit = amount * (opportunity.profit_percentage / 100)
                profit_percentage = opportunity.profit_percentage
            else:
                simulated_profit = amount * 0.0045
                profit_percentage = 0.45
            
            trade_result = {
                'status': 'executed',
                'profit': round(simulated_profit, 4),
                'profit_percentage': round(profit_percentage, 4),
                'trade_id': f'trade_{int(time.time())}',
                'triangle': triangle,
                'amount': amount,
                'exchange': exchange,
                'timestamp': time.time(),
                'note': 'Simulated execution - trading not enabled'
            }
        
        logger.info(f"✅ Trade executed: {trade_result['trade_id']} - Profit: {trade_result['profit']:.4f}")
        return Response(trade_result)
        
    except Exception as e:
        logger.error(f"❌ Trade execution failed: {e}")
        return Response({
            'status': 'failed',
            'error': str(e),
            'trade_id': None,
            'timestamp': time.time()
        }, status=400)

@api_view(['GET'])
def get_trade_history(request):
    """Get DB-backed trade history with pagination and filters"""
    try:
        qs = TradeRecord.objects.all().order_by('-timestamp')

        # Filters
        start = request.query_params.get('start_date')  # ISO date or datetime
        end = request.query_params.get('end_date')
        exchange = request.query_params.get('exchange')
        min_profit = request.query_params.get('min_profit')
        if start:
            try:
                dt = parse_datetime(start) or datetime.fromisoformat(start)
                qs = qs.filter(timestamp__gte=dt)
            except Exception:
                pass
        if end:
            try:
                dt = parse_datetime(end) or datetime.fromisoformat(end)
                qs = qs.filter(timestamp__lte=dt)
            except Exception:
                pass
        if exchange:
            qs = qs.filter(exchange__iexact=exchange)
        if min_profit:
            try:
                mp = float(min_profit)
                qs = qs.filter(profit__gte=mp)
            except Exception:
                pass

        total = qs.count()

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 25))
        offset = (page - 1) * page_size
        qs_page = qs[offset:offset + page_size]

        trades = []
        total_profit = 0.0
        total_pct = 0.0
        for t in qs_page:
            trades.append({
                'id': t.pk,
                'triangle': t.triangle,
                'entry_amount': t.entry_amount,
                'exit_amount': t.exit_amount,
                'profit': t.profit,
                'profit_percentage': t.profit_percentage,
                'status': t.status,
                'timestamp': t.timestamp.isoformat() if hasattr(t.timestamp, 'isoformat') else str(t.timestamp),
                'exchange': t.exchange,
                'error_message': t.error_message
            })
            total_profit += float(t.profit or 0.0)
            total_pct += float(t.profit_percentage or 0.0)

        average_profit_percentage = (total_pct / total) if total > 0 else 0.0

        return Response({
            'trades': trades,
            'total_trades': total,
            'total_profit': round(total_profit, 4),
            'average_profit_percentage': round(average_profit_percentage, 4),
            'page': page,
            'page_size': page_size,
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Error fetching trade history from DB: {e}")
        # fallback: existing sample payload
        sample_trades = [
            {
                'id': 'trade_123456',
                'triangle': ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'],
                'entry_amount': 1000.0,
                'exit_amount': 1004.5,
                'profit': 4.5,
                'profit_percentage': 0.45,
                'status': 'executed',
                'timestamp': '2024-01-01T12:00:00',
                'exchange': 'binance',
                'steps': ['1000.0000 USDT -> 0.0222 BTC', '0.0222 BTC -> 0.3704 ETH', '0.3704 ETH -> 1004.5000 USDT']
            }
        ]
        return Response({
            'trades': sample_trades,
            'total_trades': len(sample_trades),
            'total_profit': sum(trade['profit'] for trade in sample_trades),
            'average_profit_percentage': sum(trade['profit_percentage'] for trade in sample_trades) / len(sample_trades),
            'timestamp': time.time(),
            'note': 'Fallback - DB query failed'
        })

@api_view(['GET'])
def get_settings(request):
    """Get current settings (persisted)"""
    try:
        config, _ = BotConfig.objects.get_or_create(pk=1)
        settings = {
            'minProfitThreshold': config.min_profit_threshold,
            'maxPositionSize': config.max_position_size,
            'maxDailyLoss': config.max_daily_loss,
            'baseBalance': config.base_balance,
            'tradeSizeFraction': config.trade_size_fraction,  # NEW: Added trade size fraction
            'maxDrawdown': config.max_drawdown,
            'slippageTolerance': config.slippage_tolerance,
            'autoRestart': config.auto_restart,
            'tradingEnabled': config.trading_enabled,
            'enabledExchanges': config.enabled_exchanges_list
        }
        return Response({'settings': settings})
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return Response({'settings': {}}, status=500)

@api_view(['POST'])
@csrf_exempt
def update_settings(request):
    """Update settings persistently and apply to runtime components"""
    try:
        new_settings = request.data.get('settings', {}) or {}
        config, _ = BotConfig.objects.get_or_create(pk=1)

        # Collect fields that changed (for targeted DB update)
        update_fields = []

        # Trading Configuration
        if 'minProfitThreshold' in new_settings:
            config.min_profit_threshold = float(new_settings['minProfitThreshold'])
            # update engine runtime
            try:
                arbitrage_engine_instance.update_min_profit_threshold(config.min_profit_threshold)
            except Exception:
                logger.debug("arbitrage_engine_instance.update_min_profit_threshold not available")
            update_fields.append('min_profit_threshold')

        if 'baseBalance' in new_settings:
            config.base_balance = float(new_settings['baseBalance'])
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.current_balance = config.base_balance
                order_executor.risk_manager.peak_balance = max(order_executor.risk_manager.peak_balance, config.base_balance)
            update_fields.append('base_balance')

        if 'maxPositionSize' in new_settings:
            config.max_position_size = float(new_settings['maxPositionSize'])
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.max_position_size = config.max_position_size
            update_fields.append('max_position_size')

        if 'maxDailyLoss' in new_settings:
            config.max_daily_loss = float(new_settings['maxDailyLoss'])
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.max_daily_loss = config.max_daily_loss
            update_fields.append('max_daily_loss')

        if 'maxDrawdown' in new_settings:
            config.max_drawdown = float(new_settings['maxDrawdown'])
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.max_drawdown = config.max_drawdown
            update_fields.append('max_drawdown')

        # Trade size fraction - NEW
        if 'tradeSizeFraction' in new_settings:
            config.trade_size_fraction = float(new_settings['tradeSizeFraction'])
            update_fields.append('trade_size_fraction')

        # Additional fields from Settings UI
        if 'slippageTolerance' in new_settings:
            config.slippage_tolerance = float(new_settings['slippageTolerance'])
            update_fields.append('slippage_tolerance')

        if 'autoRestart' in new_settings:
            config.auto_restart = bool(new_settings['autoRestart'])
            update_fields.append('auto_restart')

        if 'tradingEnabled' in new_settings:
            config.trading_enabled = bool(new_settings['tradingEnabled'])
            # reflect to order_executor runtime flag
            try:
                order_executor.real_trading_enabled = config.trading_enabled
                # optionally call enable/disable APIs if exchange auth required:
                if config.trading_enabled and hasattr(order_executor, 'enable_real_trading'):
                    try:
                        order_executor.enable_real_trading()
                    except Exception:
                        logger.debug("order_executor.enable_real_trading() failed or not available")
                elif not config.trading_enabled and hasattr(order_executor, 'disable_real_trading'):
                    try:
                        order_executor.disable_real_trading()
                    except Exception:
                        logger.debug("order_executor.disable_real_trading() failed or not available")
            except Exception:
                logger.debug("Could not update order_executor.real_trading_enabled")
            update_fields.append('trading_enabled')

        if 'enabledExchanges' in new_settings:
            # Validate shape (expect list)
            exchs = new_settings['enabledExchanges'] if isinstance(new_settings['enabledExchanges'], list) else list(new_settings['enabledExchanges'])
            config.enabled_exchanges = exchs
            update_fields.append('enabled_exchanges')
            # Optionally wire exchange clients here (not forcing connections)

        if update_fields:
            config.save(update_fields=update_fields)

        logger.info(f"⚙️ Settings saved: {new_settings}")

        return Response({
            'message': 'Settings updated successfully',
            'settings': new_settings,
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"❌ Failed to update settings: {e}")
        return Response({'error': str(e)}, status=400)

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

# Add these new endpoints to views.py
@api_view(['POST'])
@csrf_exempt
def enable_real_trading(request):
    """Enable real trading mode"""
    try:
        # use module-level order_executor instance
        order_executor.enable_real_trading()
        stats = getattr(order_executor, 'get_execution_stats', lambda: {})()

        return Response({
            'status': 'success',
            'message': 'Real trading enabled',
            'real_trading': True,
            'exchanges_configured': stats.get('exchanges_configured', []),
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Failed to enable real trading: {e}")
        return Response({
            'error': f'Failed to enable real trading: {str(e)}',
            'timestamp': time.time()
        }, status=400)


@api_view(['POST'])
@csrf_exempt
def disable_real_trading(request):
    """Disable real trading mode"""
    try:
        order_executor.disable_real_trading()

        return Response({
            'status': 'success',
            'message': 'Real trading disabled',
            'real_trading': False,
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Failed to disable real trading: {e}")
        return Response({
            'error': f'Failed to disable real trading: {str(e)}',
            'timestamp': time.time()
        }, status=400)


@api_view(['GET'])
def get_risk_metrics(request):
    """Get current risk metrics"""
    try:
        rm = getattr(order_executor, 'risk_manager', None)
        if rm is None:
            raise Exception("Risk manager not available")

        # Try to call a dedicated method if available, otherwise build metrics
        risk_metrics = getattr(rm, 'get_risk_metrics', None)
        if callable(risk_metrics):
            metrics = risk_metrics()
        else:
            # Fallback: expose key attrs
            metrics = {
                'max_position_size': getattr(rm, 'max_position_size', None),
                'max_daily_loss': getattr(rm, 'max_daily_loss', None),
                'daily_pnl': getattr(rm, 'daily_pnl', None),
                'daily_trades_count': len(getattr(rm, 'daily_trades', []))
            }

        execution_stats = getattr(order_executor, 'get_execution_stats', lambda: {})()

        return Response({
            'risk_metrics': metrics,
            'execution_stats': execution_stats,
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Error fetching risk metrics: {e}")
        return Response({
            'error': str(e),
            'timestamp': time.time()
        }, status=400)


@api_view(['POST'])
@csrf_exempt
def update_risk_limits(request):
    """Update risk management limits"""
    try:
        rm = getattr(order_executor, 'risk_manager', None)
        if rm is None:
            raise Exception("Risk manager not available")

        max_position_size = request.data.get('max_position_size')
        max_daily_loss = request.data.get('max_daily_loss')
        max_drawdown = request.data.get('max_drawdown')

        # Prefer dedicated method if exists
        update_fn = getattr(rm, 'update_risk_limits', None)
        if callable(update_fn):
            update_fn(
                max_position_size=max_position_size,
                max_daily_loss=max_daily_loss,
                max_drawdown=max_drawdown
            )
        else:
            # Fallback: set attributes if provided
            if max_position_size is not None:
                rm.max_position_size = max_position_size
            if max_daily_loss is not None:
                rm.max_daily_loss = max_daily_loss
            if max_drawdown is not None:
                setattr(rm, 'max_drawdown', max_drawdown)

        return Response({
            'message': 'Risk limits updated successfully',
            'new_limits': {
                'max_position_size': getattr(rm, 'max_position_size', None),
                'max_daily_loss': getattr(rm, 'max_daily_loss', None),
                'max_drawdown': getattr(rm, 'max_drawdown', None)
            },
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Failed to update risk limits: {e}")
        return Response({
            'error': f'Failed to update risk limits: {str(e)}',
            'timestamp': time.time()
        }, status=400)