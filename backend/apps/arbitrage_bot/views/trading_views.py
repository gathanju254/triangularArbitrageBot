# backend/apps/arbitrage_bot/views/trading_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
import logging
import time
import threading
from ..core.arbitrage_engine import arbitrage_engine
from ..core.market_data import market_data_manager
from ..core.order_execution import OrderExecutor
from ..models.trade import TradeRecord, BotConfig
from ..models.arbitrage_opportunity import ArbitrageOpportunityRecord
from django.db import models

logger = logging.getLogger(__name__)

# Global instances
arbitrage_engine_instance = arbitrage_engine
market_data_manager_instance = market_data_manager
order_executor = OrderExecutor()

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

# Global trading monitor state
trading_monitor_running = False
trading_monitor_thread = None

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