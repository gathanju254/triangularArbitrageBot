# backend/apps/exchanges/views.py
from rest_framework import viewsets, status, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from .models import Exchange, MarketData, ExchangeCredentials
from .serializers import (
    ExchangeSerializer, MarketDataSerializer, 
    ExchangeCredentialsSerializer, CreateExchangeCredentialsSerializer,
    ExchangeBalanceSerializer, TickerSerializer, OrderBookSerializer,
    ExchangeStatusSerializer, TradingPairSerializer
)
from .services import ExchangeService, MarketDataService, CredentialsService
from apps.users.services import APIKeyService  # Import from users app instead
from core.permissions import IsOwnerOrAdmin, IsVerifiedUser

import logging

logger = logging.getLogger(__name__)


class ExchangeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing exchanges"""
    
    serializer_class = ExchangeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return active exchanges"""
        return Exchange.objects.filter(is_active=True)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get exchange status"""
        try:
            exchange = self.get_object()
            exchange_service = ExchangeService(exchange.id)
            status_info = exchange_service.get_exchange_status()
            
            serializer = ExchangeStatusSerializer(status_info)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def trading_pairs(self, request, pk=None):
        """Get trading pairs for exchange"""
        try:
            exchange = self.get_object()
            exchange_service = ExchangeService(exchange.id)
            pairs = exchange_service.get_trading_pairs()
            
            serializer = TradingPairSerializer(pairs, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def supported_pairs(self, request):
        """Get all supported trading pairs across exchanges"""
        exchanges = self.get_queryset()
        all_pairs = set()
        
        for exchange in exchanges:
            if exchange.supported_pairs:
                all_pairs.update(exchange.supported_pairs)
        
        return Response(sorted(list(all_pairs)))
    
    @action(detail=False, methods=['get'])
    def configured(self, request):
        """Get exchanges configured by current user"""
        configured_exchanges = Exchange.objects.filter(
            exchangecredentials__user=request.user,
            exchangecredentials__is_validated=True
        ).distinct()
        
        serializer = self.get_serializer(configured_exchanges, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_settings(self, request):
        """Get current user's exchange settings"""
        try:
            # Get all exchanges
            exchanges = self.get_queryset()
            user_settings = []
            
            for exchange in exchanges:
                # Check if user has credentials for this exchange
                try:
                    credentials = ExchangeCredentials.objects.get(
                        user=request.user,
                        exchange=exchange
                    )
                    enabled = True  # If credentials exist, exchange is enabled
                    trading_enabled = credentials.trading_enabled
                except ExchangeCredentials.DoesNotExist:
                    enabled = False
                    trading_enabled = False
                
                # Add exchange settings
                user_settings.append({
                    'name': exchange.code,
                    'enabled': enabled,
                    'tradingEnabled': trading_enabled,
                    'maxTradeSize': 1000,  # Default value
                    'minProfitThreshold': 0.5,  # Default value
                    'exchange_info': {
                        'id': exchange.id,
                        'name': exchange.name,
                        'code': exchange.code,
                        'type': exchange.exchange_type,
                        'trading_fee': float(exchange.trading_fee),
                        'is_active': exchange.is_active
                    }
                })
            
            return Response({
                'exchanges': user_settings,
                'last_updated': timezone.now()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch user settings: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def user_exchange_settings(self, request):
        """Get current user's exchange settings in frontend-compatible format"""
        try:
            # Get all exchanges
            exchanges = Exchange.objects.filter(is_active=True)
            user_settings = []
            
            for exchange in exchanges:
                # Check if user has credentials for this exchange
                try:
                    credentials = ExchangeCredentials.objects.get(
                        user=request.user,
                        exchange=exchange
                    )
                    enabled = True
                    trading_enabled = credentials.trading_enabled
                except ExchangeCredentials.DoesNotExist:
                    enabled = False
                    trading_enabled = False
                
                # Add exchange settings in frontend-compatible format
                user_settings.append({
                    'name': exchange.code,  # Use code instead of name for consistency
                    'enabled': enabled,
                    'tradingEnabled': trading_enabled,
                    'maxTradeSize': 1000,  # Default value
                    'minProfitThreshold': 0.5,  # Default value
                    'exchange_info': {
                        'id': exchange.id,
                        'name': exchange.name,
                        'code': exchange.code,
                        'type': exchange.exchange_type,
                        'trading_fee': float(exchange.trading_fee),
                        'is_active': exchange.is_active
                    }
                })
            
            return Response({
                'exchanges': user_settings,
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch user settings: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['put'])
    def update_user_settings(self, request):
        """Update exchange settings from frontend"""
        try:
            exchange_settings = request.data.get('exchanges', [])
            print(f"📥 Received exchange settings from frontend: {exchange_settings}")
            
            if not isinstance(exchange_settings, list):
                return Response(
                    {'error': 'exchanges must be a list'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            updated_exchanges = []
            
            with transaction.atomic():
                for setting in exchange_settings:
                    exchange_name = setting.get('name')
                    enabled = setting.get('enabled', False)
                    trading_enabled = setting.get('tradingEnabled', False)
                    
                    if not exchange_name:
                        continue
                        
                    print(f"🔄 Processing exchange: {exchange_name}, enabled: {enabled}")
                    
                    try:
                        # Get the exchange object
                        exchange = Exchange.objects.get(code=exchange_name, is_active=True)
                        
                        if enabled:
                            # Check if credentials already exist
                            credentials, created = ExchangeCredentials.objects.get_or_create(
                                user=request.user,
                                exchange=exchange,
                                defaults={
                                    'trading_enabled': trading_enabled,
                                    'withdrawal_enabled': False,
                                    'is_validated': False,
                                    'validation_message': 'Credentials not yet validated'
                                }
                            )
                            
                            # Update existing credentials
                            if not created:
                                credentials.trading_enabled = trading_enabled
                                credentials.save()
                                print(f"✅ Updated credentials for {exchange_name}")
                            else:
                                print(f"✅ Created new credentials for {exchange_name}")
                        else:
                            # Disable by deleting credentials
                            deleted_count, _ = ExchangeCredentials.objects.filter(
                                user=request.user,
                                exchange=exchange
                            ).delete()
                            print(f"🗑️ Disabled exchange {exchange_name}, deleted: {deleted_count}")
                        
                        updated_exchanges.append({
                            'name': exchange.name,
                            'code': exchange.code,
                            'enabled': enabled,
                            'trading_enabled': trading_enabled
                        })
                        
                    except Exchange.DoesNotExist:
                        print(f"❌ Exchange not found: {exchange_name}")
                        continue
                    except Exception as e:
                        print(f"❌ Error updating exchange {exchange_name}: {str(e)}")
                        import traceback
                        print(f"Full error: {traceback.format_exc()}")
                        continue
                
            print(f"✅ Successfully updated {len(updated_exchanges)} exchanges")
            
            return Response({
                'message': 'Exchange settings updated successfully',
                'updated_exchanges': updated_exchanges,
                'total_updated': len(updated_exchanges)
            })
            
        except Exception as e:
            print(f"❌ Failed to update exchange settings: {str(e)}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            return Response(
                {'error': f'Failed to update exchange settings: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def test_settings(self, request):
        """Test endpoint to verify settings are being received"""
        try:
            print("📥 Received data:", request.data)
            print("📥 Headers:", request.headers)
            print("👤 User:", request.user.username)
            
            return Response({
                'received_data': request.data,
                'user': request.user.username,
                'message': 'Settings received successfully'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def echo_settings(self, request):
        """Echo back the received settings for testing"""
        try:
            print("📨 Echo endpoint called")
            print("📥 Request data:", request.data)
            print("👤 User:", request.user.username)
            print("🔑 Auth:", request.auth)
            
            return Response({
                'received': request.data,
                'user': request.user.username,
                'user_id': request.user.id,
                'timestamp': timezone.now().isoformat(),
                'message': 'Echo successful'
            })
        except Exception as e:
            print(f"❌ Echo error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class MarketDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for market data"""
    
    serializer_class = MarketDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return market data with filters"""
        queryset = MarketData.objects.select_related('exchange')
        
        # Filter by symbol if provided
        symbol = self.request.query_params.get('symbol')
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        
        # Filter by exchange if provided
        exchange_id = self.request.query_params.get('exchange_id')
        if exchange_id:
            queryset = queryset.filter(exchange_id=exchange_id)
        
        # Only return fresh data by default
        fresh_only = self.request.query_params.get('fresh_only', 'true').lower() == 'true'
        if fresh_only:
            queryset = queryset.filter(is_fresh=True)
        
        # Limit to recent data
        hours = int(self.request.query_params.get('hours', 24))
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)
        queryset = queryset.filter(timestamp__gte=time_threshold)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest market data for all symbols"""
        # Get unique symbols
        symbols = MarketData.objects.filter(is_fresh=True).values_list(
            'symbol', flat=True
        ).distinct()
        
        latest_data = []
        for symbol in symbols:
            try:
                latest = MarketData.objects.filter(
                    symbol=symbol, is_fresh=True
                ).select_related('exchange').latest('timestamp')
                latest_data.append(latest)
            except MarketData.DoesNotExist:
                continue
        
        serializer = self.get_serializer(latest_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tickers(self, request):
        """Get ticker data for symbols"""
        symbol = request.query_params.get('symbol')
        exchange_id = request.query_params.get('exchange_id')
        
        if not symbol:
            return Response(
                {'error': 'Symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            market_data_service = MarketDataService()
            tickers = market_data_service.get_ticker_data(symbol, exchange_id)
            
            serializer = TickerSerializer(tickers, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def orderbook(self, request):
        """Get order book for a symbol"""
        symbol = request.query_params.get('symbol')
        exchange_id = request.query_params.get('exchange_id')
        
        if not symbol or not exchange_id:
            return Response(
                {'error': 'Symbol and exchange_id parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            exchange_service = ExchangeService(exchange_id)
            orderbook = exchange_service.get_order_book(symbol)
            
            serializer = OrderBookSerializer(orderbook)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ExchangeCredentialsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing exchange credentials"""
    
    permission_classes = [IsAuthenticated, IsVerifiedUser, IsOwnerOrAdmin]
    
    def get_queryset(self):
        """Return credentials for current user"""
        return ExchangeCredentials.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return CreateExchangeCredentialsSerializer
        return ExchangeCredentialsSerializer
    
    def perform_create(self, serializer):
        """Create credentials and validate them"""
        credentials = serializer.save()
        
        # Validate credentials
        try:
            credentials_service = CredentialsService(credentials)
            credentials_service.validate_credentials()
        except Exception as e:
            # Credentials will be saved but marked as invalid
            credentials.validation_message = str(e)
            credentials.save()
    
    @action(detail=False, methods=['post'], url_path='validate')
    def validate(self, request):
        """Validate API key credentials without creating ExchangeCredentials"""
        try:
            logger.info(f"🔍 Validating exchange credentials for user: {request.user.username}")
            logger.debug(f"Request data: {request.data}")

            # Use serializer and raise structured validation errors
            serializer = ExchangeCredentialsSerializer(data=request.data, context={'request': request})
            try:
                serializer.is_valid(raise_exception=True)
            except drf_serializers.ValidationError as exc:
                logger.warning(f"❌ Validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            exchange = data.get('exchange')
            api_key = data.get('api_key')
            secret = data.get('secret_key')
            passphrase = data.get('passphrase')

            # Use centralized service for validation (keeps logic consistent)
            is_valid, details = APIKeyService.validate_api_key_with_exchange(
                exchange=exchange,
                api_key=api_key,
                secret_key=secret,
                passphrase=passphrase
            )

            # Normalize error message for frontend convenience
            error_msg = None
            if isinstance(details, dict):
                if details.get('error'):
                    error_msg = details.get('error')
                elif details.get('errors'):
                    # join list into readable string
                    errs = details.get('errors')
                    error_msg = '; '.join(errs) if isinstance(errs, (list, tuple)) else str(errs)
                elif details.get('message'):
                    error_msg = details.get('message')

            result = {
                'valid': bool(is_valid),
                'exchange': exchange,
                'permissions': (details or {}).get('permissions', []),
                'account_type': (details or {}).get('account_type', 'unknown'),
                'error': error_msg,
                'timestamp': (details or {}).get('timestamp'),
                'details': details or {}
            }

            logger.info(f"✅ Validation completed: {result['valid']}")
            return Response(result)

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get balance for exchange"""
        try:
            credentials = self.get_object()
            
            if not credentials.is_validated:
                return Response(
                    {'error': 'Credentials are not validated'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            exchange_service = ExchangeService(credentials.exchange_id)
            balance_info = exchange_service.get_balance(credentials)
            
            serializer = ExchangeBalanceSerializer(balance_info)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def toggle_trading(self, request, pk=None):
        """Toggle trading permission"""
        credentials = self.get_object()
        credentials.trading_enabled = not credentials.trading_enabled
        credentials.save()
        
        message = "Trading enabled" if credentials.trading_enabled else "Trading disabled"
        return Response({'message': message})
    
    @action(detail=True, methods=['post'])
    def toggle_withdrawal(self, request, pk=None):
        """Toggle withdrawal permission"""
        credentials = self.get_object()
        credentials.withdrawal_enabled = not credentials.withdrawal_enabled
        credentials.save()
        
        message = "Withdrawal enabled" if credentials.withdrawal_enabled else "Withdrawal disabled"
        return Response({'message': message})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of all user's exchange credentials"""
        credentials = self.get_queryset().select_related('exchange')
        
        summary_data = {
            'total_credentials': credentials.count(),
            'validated_credentials': credentials.filter(is_validated=True).count(),
            'trading_enabled': credentials.filter(trading_enabled=True).count(),
            'exchanges': []
        }
        
        for cred in credentials:
            summary_data['exchanges'].append({
                'exchange_name': cred.exchange.name,
                'is_validated': cred.is_validated,
                'trading_enabled': cred.trading_enabled,
                'last_validation': cred.last_validation,
                'validation_message': cred.validation_message
            })
        
        return Response(summary_data)


class ExchangeOperationsViewSet(viewsets.ViewSet):
    """ViewSet for exchange operations"""
    
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    
    @action(detail=False, methods=['get'])
    def balances(self, request):
        """Get balances across all configured exchanges"""
        credentials = ExchangeCredentials.objects.filter(
            user=request.user,
            is_validated=True
        ).select_related('exchange')
        
        all_balances = []
        total_balance_usd = 0
        
        for credential in credentials:
            try:
                exchange_service = ExchangeService(credential.exchange_id)
                balance_info = exchange_service.get_balance(credential)
                all_balances.append(balance_info)
                total_balance_usd += float(balance_info['total_balance_usd'])
            except Exception as e:
                # Skip exchanges that fail
                continue
        
        return Response({
            'balances': all_balances,
            'total_balance_usd': total_balance_usd
        })
    
    @action(detail=False, methods=['get'])
    def test_connectivity(self, request):
        """Test connectivity to all configured exchanges"""
        credentials = ExchangeCredentials.objects.filter(
            user=request.user,
            is_validated=True
        ).select_related('exchange')
        
        connectivity_results = []
        
        for credential in credentials:
            try:
                exchange_service = ExchangeService(credential.exchange_id)
                status_info = exchange_service.get_exchange_status()
                
                connectivity_results.append({
                    'exchange': credential.exchange.name,
                    'is_online': status_info['is_online'],
                    'response_time_ms': status_info['response_time_ms'],
                    'message': status_info.get('message', 'Connected successfully')
                })
                
            except Exception as e:
                connectivity_results.append({
                    'exchange': credential.exchange.name,
                    'is_online': False,
                    'response_time_ms': 0,
                    'message': str(e)
                })
        
        return Response(connectivity_results)
    
    @action(detail=False, methods=['post'])
    def sync_market_data(self, request):
        """Trigger market data sync for all exchanges"""
        try:
            from .tasks import sync_all_exchanges_market_data
            sync_all_exchanges_market_data.delay()
            
            return Response({'message': 'Market data sync initiated'})
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def exchange_status(self, request):
        """Get status for all exchanges"""
        try:
            from .services import ExchangeFactory
            exchange_services = ExchangeFactory.get_all_active_exchanges()
            
            status_results = []
            for exchange_service in exchange_services:
                try:
                    status_info = exchange_service.get_exchange_status()
                    status_results.append({
                        'exchange': exchange_service.exchange.name,
                        'is_online': status_info['is_online'],
                        'response_time_ms': status_info['response_time_ms'],
                        'maintenance_mode': status_info.get('maintenance_mode', False),
                        'message': status_info.get('message', '')
                    })
                except Exception as e:
                    status_results.append({
                        'exchange': exchange_service.exchange.name,
                        'is_online': False,
                        'response_time_ms': 0,
                        'maintenance_mode': False,
                        'message': str(e)
                    })
            
            return Response(status_results)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get exchange status: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )