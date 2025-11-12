# backend/apps/exchanges/views_integration.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.utils import timezone

from .models import Exchange
from .serializers import ExchangeSerializer
from .services import ExchangeFactory, exchange_api_integration
from .permissions import IsVerifiedUser

import logging

logger = logging.getLogger(__name__)


class UserExchangeIntegrationViewSet(viewsets.ViewSet):
    """ViewSet for user-specific exchange operations using database API keys"""
    
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    
    @action(detail=False, methods=['get'])
    def my_exchanges(self, request):
        """Get exchanges where user has configured API keys"""
        try:
            user_exchanges = exchange_api_integration.get_user_exchanges_with_keys(request.user)
            
            return Response({
                'exchanges': user_exchanges,
                'total_count': len(user_exchanges),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get user exchanges: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def balances(self, request):
        """Get balances across all user's configured exchanges"""
        try:
            exchange_services = ExchangeFactory.get_user_exchanges_with_keys(request.user)
            all_balances = []
            total_balance_usd = 0
            
            for exchange_service in exchange_services:
                try:
                    balance_info = exchange_service.get_user_balance()
                    all_balances.append(balance_info)
                    total_balance_usd += float(balance_info['total_balance_usd'])
                except Exception as e:
                    logger.error(f"Failed to get balance for {exchange_service.exchange.name}: {e}")
                    continue
            
            return Response({
                'balances': all_balances,
                'total_balance_usd': total_balance_usd,
                'exchange_count': len(all_balances),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get user balances: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def connection_status(self, request):
        """Get connection status for all user's configured exchanges"""
        try:
            user_exchanges = exchange_api_integration.get_user_exchanges_with_keys(request.user)
            connection_status = []
            
            for exchange_info in user_exchanges:
                try:
                    exchange_service = ExchangeFactory.get_exchange_by_code(
                        exchange_info['exchange_code'], 
                        user=request.user
                    )
                    status_info = exchange_service.validate_user_connection()
                    connection_status.append(status_info)
                except Exception as e:
                    connection_status.append({
                        'exchange': exchange_info['exchange_code'],
                        'connected': False,
                        'error': str(e),
                        'timestamp': timezone.now().isoformat()
                    })
            
            return Response({
                'connections': connection_status,
                'total_connected': sum(1 for conn in connection_status if conn.get('connected', False)),
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get connection status: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def test_connection(self, request, pk=None):
        """Test connection to a specific exchange using user's API keys"""
        try:
            exchange = Exchange.objects.get(id=pk, is_active=True)
            exchange_service = ExchangeFactory.get_exchange_by_code(exchange.code, user=request.user)
            
            status_info = exchange_service.validate_user_connection()
            
            return Response(status_info)
            
        except Exchange.DoesNotExist:
            return Response(
                {'error': 'Exchange not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get balance for a specific exchange using user's API keys"""
        try:
            exchange = Exchange.objects.get(id=pk, is_active=True)
            exchange_service = ExchangeFactory.get_exchange_by_code(exchange.code, user=request.user)
            
            balance_info = exchange_service.get_user_balance()
            
            return Response(balance_info)
            
        except Exchange.DoesNotExist:
            return Response(
                {'error': 'Exchange not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Balance fetch failed: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ExchangeConnectorViewSet(viewsets.ViewSet):
    """ViewSet for exchange connector operations"""
    
    permission_classes = [IsAuthenticated, IsVerifiedUser]
    
    @action(detail=False, methods=['post'])
    def create_connector(self, request):
        """Create an exchange connector for trading operations"""
        try:
            exchange_code = request.data.get('exchange_code')
            if not exchange_code:
                return Response(
                    {'error': 'exchange_code is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            connector = exchange_api_integration.create_exchange_connector(
                user=request.user,
                exchange_code=exchange_code
            )
            
            if not connector:
                return Response(
                    {'error': f'Failed to create connector for {exchange_code}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Test the connector
            try:
                status_info = connector.get_exchange_status()
                balance = connector.get_balance() if connector.api_key else {}
                
                return Response({
                    'exchange': exchange_code,
                    'connector_created': True,
                    'authenticated': bool(connector.api_key),
                    'status': status_info,
                    'has_balance_access': bool(balance),
                    'timestamp': timezone.now().isoformat()
                })
                
            except Exception as e:
                return Response({
                    'exchange': exchange_code,
                    'connector_created': True,
                    'authenticated': bool(connector.api_key),
                    'error': f'Connector test failed: {str(e)}',
                    'timestamp': timezone.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Failed to create exchange connector: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )