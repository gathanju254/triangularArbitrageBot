# backend/apps/users/views/settings_views.py
import logging
import time
import json
from rest_framework import status, permissions
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from ..services.settings_service import SettingsService
from ..serializers.settings_serializers import (
    UserSettingsSerializer,
    TradingSettingsSerializer,
    RiskSettingsSerializer,
    NotificationSettingsSerializer,
    ExchangeSettingsSerializer,
    BotConfigurationSerializer
)
from ..models.settings import BotConfiguration, UserSettings
from apps.arbitrage_bot.core.order_execution import OrderExecutor

logger = logging.getLogger(__name__)

order_executor = OrderExecutor()

class UserSettingsViewSet(ViewSet):
    """Professional settings management API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get all user settings"""
        try:
            settings = SettingsService.get_user_settings(request.user)
            serializer = UserSettingsSerializer(settings)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to get user settings: {e}")
            return Response(
                {'error': 'Failed to load settings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get', 'put'])
    def trading(self, request):
        """Get or update trading settings"""
        if request.method == 'GET':
            try:
                settings = SettingsService.get_user_settings(request.user)
                serializer = TradingSettingsSerializer(settings)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Failed to get trading settings: {e}")
                return Response(
                    {'error': 'Failed to load trading settings'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif request.method == 'PUT':
            try:
                serializer = TradingSettingsSerializer(data=request.data)
                if serializer.is_valid():
                    settings = SettingsService.update_user_settings(
                        request.user, 
                        serializer.validated_data
                    )
                    return Response(TradingSettingsSerializer(settings).data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Failed to update trading settings: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=False, methods=['get', 'put'])
    def risk(self, request):
        """Get or update risk management settings"""
        if request.method == 'GET':
            try:
                settings = SettingsService.get_user_settings(request.user)
                serializer = RiskSettingsSerializer(settings)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Failed to get risk settings: {e}")
                return Response(
                    {'error': 'Failed to load risk settings'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif request.method == 'PUT':
            try:
                serializer = RiskSettingsSerializer(data=request.data)
                if serializer.is_valid():
                    settings = SettingsService.update_user_settings(
                        request.user, 
                        serializer.validated_data
                    )
                    return Response(RiskSettingsSerializer(settings).data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Failed to update risk settings: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=False, methods=['get', 'put'])
    def notifications(self, request):
        """Get or update notification settings"""
        if request.method == 'GET':
            try:
                settings = SettingsService.get_user_settings(request.user)
                serializer = NotificationSettingsSerializer(settings)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Failed to get notification settings: {e}")
                return Response(
                    {'error': 'Failed to load notification settings'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif request.method == 'PUT':
            try:
                serializer = NotificationSettingsSerializer(data=request.data)
                if serializer.is_valid():
                    settings = SettingsService.update_user_settings(
                        request.user, 
                        serializer.validated_data
                    )
                    return Response(NotificationSettingsSerializer(settings).data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Failed to update notification settings: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=False, methods=['get', 'put'])
    def exchanges(self, request):
        """Get or update exchange settings"""
        if request.method == 'GET':
            try:
                settings = SettingsService.get_user_settings(request.user)
                serializer = ExchangeSettingsSerializer(settings)
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Failed to get exchange settings: {e}")
                return Response(
                    {'error': 'Failed to load exchange settings'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        elif request.method == 'PUT':
            try:
                # Handle both user preferences and system-enabled exchanges
                user_data = {
                    'preferred_exchanges': request.data.get('preferred_exchanges'),
                    'min_profit_threshold': request.data.get('min_profit_threshold')
                }
                
                # Update user settings
                settings = SettingsService.update_user_settings(request.user, user_data)
                
                # Update system configuration if enabled_exchanges provided
                if 'enabled_exchanges' in request.data:
                    system_data = {
                        'enabled_exchanges': request.data.get('enabled_exchanges')
                    }
                    SettingsService.update_bot_configuration(system_data)
                
                return Response(ExchangeSettingsSerializer(settings).data)
            except Exception as e:
                logger.error(f"Failed to update exchange settings: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=False, methods=['post'])
    def reset(self, request):
        """Reset all settings to defaults"""
        try:
            settings = SettingsService.reset_to_defaults(request.user)
            serializer = UserSettingsSerializer(settings)
            return Response({
                'message': 'Settings reset to defaults successfully',
                'settings': serializer.data
            })
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return Response(
                {'error': 'Failed to reset settings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export settings for backup"""
        try:
            export_data = SettingsService.export_user_settings(request.user)
            return Response(export_data)
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return Response(
                {'error': 'Failed to export settings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BotConfigurationViewSet(ViewSet):
    """System-wide bot configuration API (admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def list(self, request):
        """Get bot configuration"""
        try:
            config = SettingsService.get_bot_configuration()
            serializer = BotConfigurationSerializer(config)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Failed to get bot configuration: {e}")
            return Response(
                {'error': 'Failed to load bot configuration'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request):
        """Update bot configuration"""
        try:
            serializer = BotConfigurationSerializer(data=request.data)
            if serializer.is_valid():
                config = SettingsService.update_bot_configuration(
                    serializer.validated_data
                )
                return Response(BotConfigurationSerializer(config).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Failed to update bot configuration: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# Legacy API endpoints for backward compatibility
@api_view(['GET'])
def get_settings(request):
    """Legacy endpoint: Get current settings (persisted)"""
    try:
        config = BotConfiguration.get_config()
        settings = {
            'minProfitThreshold': 0.3,  # Default value
            'minTradeAmount': 10.0,     # Default value
            'maxPositionSize': 100.0,   # Default value
            'maxDailyLoss': 50.0,       # Default value
            'baseBalance': float(config.base_balance),
            'tradeSizeFraction': float(config.trade_size_fraction),
            'maxDrawdown': 20.0,        # Default value
            'slippageTolerance': 0.1,   # Default value
            'autoRestart': config.auto_restart,
            'tradingEnabled': config.trading_enabled,
            'enabledExchanges': config.enabled_exchanges if config.enabled_exchanges else ['binance']
        }
        return Response({'settings': settings})
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        return Response({'settings': {}}, status=500)

@api_view(['POST'])
@csrf_exempt
def update_settings(request):
    """Legacy endpoint: Update settings persistently and apply to runtime components"""
    try:
        new_settings = request.data.get('settings', {}) or {}
        config = BotConfiguration.get_config()

        # Collect fields that changed
        update_fields = []

        # Enhanced logging for settings update
        logger.info(f"⚙️ Settings update requested: {new_settings}")

        # Trading Configuration with validation
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

        # Calculate and log actual trade size
        actual_trade_size = config.base_balance * config.trade_size_fraction
        logger.info(f"🎯 Calculated trade size: ${actual_trade_size:.2f} (${config.base_balance} * {config.trade_size_fraction*100}%)")

        # Trading Configuration
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
            config.save()

        # Verify settings were applied
        logger.info(f"✅ Settings saved successfully: {len(update_fields)} fields updated")

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
            config = BotConfiguration.get_config()
            
            if getattr(config, 'trading_enabled', False):
                for exchange in getattr(config, 'enabled_exchanges', ['binance']):
                    balance_data = rm.get_exchange_balance(exchange)
                    exchange_balances[exchange] = balance_data
        except Exception as e:
            logger.warning(f"Could not fetch exchange balances: {e}")

        execution_stats = getattr(order_executor, 'get_execution_stats', lambda: {})()

        return Response({
            'risk_metrics': risk_metrics,
            'exchange_balances': exchange_balances,
            'execution_stats': execution_stats,
            'timestamp': time.time()
        })

    except Exception as e:
        logger.error(f"Error fetching risk metrics: {e}")
        return Response({
            'error': str(e),
            'timestamp': time.time()
        }, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def get_trading_config(request):
    """Legacy endpoint: Get trading configuration with expanded settings"""
    try:
        config = BotConfiguration.get_config()
        
        config_data = {
            "auto_trading": config.trading_enabled,
            "trading_mode": "full-auto" if config.trading_enabled else "manual",
            "max_concurrent_trades": 3,  # Default value
            "min_trade_amount": 10.0,    # Default value
            "stop_loss_enabled": True,
            "take_profit_enabled": True,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 5.0,
            "email_notifications": True,
            "push_notifications": False,
            "trading_alerts": True,
            "risk_alerts": True,
            "slippage_tolerance": 0.1
        }
        return JsonResponse(config_data)
    except Exception as e:
        logger.error(f"Error fetching trading config: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_trading_config(request):
    """Legacy endpoint: Update trading configuration with validation"""
    try:
        data = json.loads(request.body)
        config = BotConfiguration.get_config()
        
        # Update fields with validation
        if 'auto_trading' in data:
            config.trading_enabled = bool(data['auto_trading'])
        
        if 'slippage_tolerance' in data:
            config.slippage_tolerance = float(data['slippage_tolerance'])
        
        # Save changes
        config.save()
        
        return JsonResponse({
            "status": "success",
            "message": "Trading configuration updated successfully",
            "config": {
                "auto_trading": config.trading_enabled,
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