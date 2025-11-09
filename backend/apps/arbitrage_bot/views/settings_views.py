# backend/apps/arbitrage_bot/views/settings_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import logging
import time
import json
from ..models.trade import BotConfig
from ..core.order_execution import OrderExecutor

logger = logging.getLogger(__name__)

order_executor = OrderExecutor()

@api_view(['GET'])
def get_settings(request):
    """Get current settings (persisted)"""
    try:
        config, _ = BotConfig.objects.get_or_create(pk=1)
        settings = {
            'minProfitThreshold': config.min_profit_threshold,
            'minTradeAmount': config.min_trade_amount,
            'maxPositionSize': config.max_position_size,
            'maxDailyLoss': config.max_daily_loss,
            'baseBalance': config.base_balance,
            'tradeSizeFraction': config.trade_size_fraction,
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

        # Collect fields that changed
        update_fields = []

        # Enhanced logging for settings update
        logger.info(f"⚙️ Settings update requested: {new_settings}")

        # Trading Configuration with validation
        if 'minProfitThreshold' in new_settings:
            new_threshold = float(new_settings['minProfitThreshold'])
            if new_threshold < 0.01:
                return Response({'error': 'Minimum profit threshold must be at least 0.01%'}, status=400)
            config.min_profit_threshold = new_threshold
            arbitrage_engine_instance.update_min_profit_threshold(new_threshold)
            update_fields.append('min_profit_threshold')
            logger.info(f"📈 Min profit threshold updated to {new_threshold}%")

        if 'maxPositionSize' in new_settings:
            new_size = float(new_settings['maxPositionSize'])
            if new_size < 2:  # Minimum $2 per trade
                return Response({'error': 'Maximum position size must be at least $2'}, status=400)
            config.max_position_size = new_size
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.max_position_size = new_size
            update_fields.append('max_position_size')
            logger.info(f"💰 Max position size updated to ${new_size}")

        if 'baseBalance' in new_settings:
            new_balance = float(new_settings['baseBalance'])
            config.base_balance = new_balance
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.current_balance = new_balance
                order_executor.risk_manager.peak_balance = max(order_executor.risk_manager.peak_balance, new_balance)
            update_fields.append('base_balance')
            logger.info(f"💳 Base balance updated to ${new_balance}")

        if 'tradeSizeFraction' in new_settings:
            new_fraction = float(new_settings['tradeSizeFraction'])
            if new_fraction <= 0 or new_fraction > 1:
                return Response({'error': 'Trade size fraction must be between 0.01 and 1.00'}, status=400)
            config.trade_size_fraction = new_fraction
            update_fields.append('trade_size_fraction')
            logger.info(f"📊 Trade size fraction updated to {new_fraction*100}%")

        if 'minTradeAmount' in new_settings:
            new_min = float(new_settings['minTradeAmount'])
            # enforce minimum of $1.01 (require > $1)
            if new_min <= 1.0:
                return Response({'error': 'Minimum trade amount must be greater than $1'}, status=400)
            config.min_trade_amount = new_min
            update_fields.append('min_trade_amount')
            # Apply to runtime RiskManager if available
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.min_trade_amount = new_min
            logger.info(f"🪙 Min trade amount updated to ${config.min_trade_amount}")

        # Calculate and log actual trade size
        actual_trade_size = config.base_balance * config.trade_size_fraction
        logger.info(f"🎯 Calculated trade size: ${actual_trade_size:.2f} (${config.base_balance} * {config.trade_size_fraction*100}%)")

        # Risk Management Settings
        if 'maxDailyLoss' in new_settings:
            config.max_daily_loss = float(new_settings['maxDailyLoss'])
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.max_daily_loss = config.max_daily_loss
            update_fields.append('max_daily_loss')
            logger.info(f"🛡️ Max daily loss updated to ${config.max_daily_loss}")

        if 'maxDrawdown' in new_settings:
            config.max_drawdown = float(new_settings['maxDrawdown'])
            if hasattr(order_executor, 'risk_manager') and order_executor.risk_manager:
                order_executor.risk_manager.max_drawdown = config.max_drawdown
            update_fields.append('max_drawdown')
            logger.info(f"📉 Max drawdown updated to {config.max_drawdown}%")

        # Trading Configuration
        if 'slippageTolerance' in new_settings:
            config.slippage_tolerance = float(new_settings['slippageTolerance'])
            update_fields.append('slippage_tolerance')
            logger.info(f"🎯 Slippage tolerance updated to {config.slippage_tolerance}%")

        if 'autoRestart' in new_settings:
            config.auto_restart = bool(new_settings['autoRestart'])
            update_fields.append('auto_restart')
            logger.info(f"🔄 Auto restart updated to {config.auto_restart}")

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
            logger.info(f"🔐 Trading enabled updated to {config.trading_enabled}")

        if 'enabledExchanges' in new_settings:
            # Validate shape (expect list)
            exchs = new_settings['enabledExchanges'] if isinstance(new_settings['enabledExchanges'], list) else list(new_settings['enabledExchanges'])
            config.enabled_exchanges = exchs
            update_fields.append('enabled_exchanges')
            logger.info(f"🏦 Enabled exchanges updated to {exchs}")

        if update_fields:
            config.save(update_fields=update_fields)

        # Verify settings were applied
        logger.info(f"✅ Settings saved successfully: {len(update_fields)} fields updated")
        logger.info(f"🔍 Final verification - Max Position: ${config.max_position_size}, Min Trade: ${getattr(order_executor, 'min_trade_amount', 'N/A')}")

        return Response({
            'message': 'Settings updated successfully',
            'settings': new_settings,
            'calculated_trade_size': round(actual_trade_size, 2),
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"❌ Failed to update settings: {e}")
        return Response({'error': str(e)}, status=400)

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
    """Get current risk metrics including real exchange balances"""
    try:
        rm = getattr(order_executor, 'risk_manager', None)
        if rm is None:
            raise Exception("Risk manager not available")

        # Get standard risk metrics
        risk_metrics = rm.get_risk_metrics() if hasattr(rm, 'get_risk_metrics') else {}
        
        # Get real exchange balances if trading is enabled
        exchange_balances = {}
        try:
            from .models.trade import BotConfig
            cfg, _ = BotConfig.objects.get_or_create(pk=1)
            
            if getattr(cfg, 'trading_enabled', False):
                for exchange in getattr(cfg, 'enabled_exchanges', ['binance']):
                    balance_data = rm.get_exchange_balance(exchange)
                    exchange_balances[exchange] = balance_data
        except Exception as e:
            logger.warning(f"Could not fetch exchange balances: {e}")

        execution_stats = getattr(order_executor, 'get_execution_stats', lambda: {})()

        return Response({
            'risk_metrics': risk_metrics,
            'exchange_balances': exchange_balances,  # NEW: Include exchange balances
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

@csrf_exempt
@require_http_methods(["GET"])
def get_trading_config(request):
    """Get trading configuration with expanded settings"""
    try:
        config, _ = BotConfig.objects.get_or_create(pk=1)
        
        config_data = {
            "auto_trading": config.trading_enabled,
            "trading_mode": "full-auto" if config.trading_enabled else "manual",
            "max_concurrent_trades": getattr(config, 'max_concurrent_trades', 3),
            "min_trade_amount": config.min_trade_amount,
            "stop_loss_enabled": True,
            "take_profit_enabled": True,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 5.0,
            "email_notifications": True,
            "push_notifications": False,
            "trading_alerts": True,
            "risk_alerts": True,
            "slippage_tolerance": config.slippage_tolerance
        }
        return JsonResponse(config_data)
    except Exception as e:
        logger.error(f"Error fetching trading config: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_trading_config(request):
    """Update trading configuration with validation"""
    try:
        data = json.loads(request.body)
        config, _ = BotConfig.objects.get_or_create(pk=1)
        
        # Update fields with validation
        if 'auto_trading' in data:
            config.trading_enabled = bool(data['auto_trading'])
        
        if 'min_trade_amount' in data:
            new_min = float(data['min_trade_amount'])
            if new_min <= 1.0:
                return JsonResponse({
                    "status": "error",
                    "message": "Minimum trade amount must be greater than $1"
                }, status=400)
            config.min_trade_amount = new_min
            
        if 'max_concurrent_trades' in data:
            config.max_concurrent_trades = int(data['max_concurrent_trades'])
            
        if 'slippage_tolerance' in data:
            config.slippage_tolerance = float(data['slippage_tolerance'])
        
        # Save changes
        config.save()
        
        return JsonResponse({
            "status": "success",
            "message": "Trading configuration updated successfully",
            "config": {
                "auto_trading": config.trading_enabled,
                "min_trade_amount": config.min_trade_amount,
                "max_concurrent_trades": config.max_concurrent_trades,
                "slippage_tolerance": config.slippage_tolerance
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            "status": "error",
            "message": f"Invalid value provided: {str(e)}"
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating trading config: {e}")
        return JsonResponse({
            "status": "error",
            "message": f"Failed to update configuration: {str(e)}"
        }, status=500)