# backend/apps/users/views/admin_views.py
import logging
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

from ..models import User, APIKey, UserProfile
from ..serializers import (
    UserSerializer, APIKeySerializer, UserProfileSerializer
)
from ..services.user_service import UserService
from ..services.api_key_service import APIKeyService

logger = logging.getLogger(__name__)


class UserAdminViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for user management (staff only).
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account"""
        user = self.get_object()
        
        try:
            success = UserService.deactivate_user(user)
            
            if success:
                return Response({
                    'message': f'User {user.username} deactivated successfully'
                })
            else:
                return Response({
                    'error': 'Failed to deactivate user'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"❌ Failed to deactivate user {user.username}: {e}")
            return Response({
                'error': f'Deactivation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user statistics for admin dashboard"""
        try:
            # User counts
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            verified_users = User.objects.filter(is_verified=True).count()
            
            # Recent activity
            thirty_days_ago = timezone.now() - timedelta(days=30)
            new_users_30d = User.objects.filter(
                date_joined__gte=thirty_days_ago
            ).count()
            
            # User types
            user_types = User.objects.values('user_type').annotate(
                count=Count('id')
            )
            
            # Recent registrations
            recent_users = User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=7)
            ).order_by('-date_joined')
            
            recent_users_data = UserSerializer(recent_users, many=True).data
            
            stats = {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'new_users_30d': new_users_30d,
                'user_types': list(user_types),
                'recent_registrations': recent_users_data,
                'registration_trend': {
                    'today': User.objects.filter(
                        date_joined__date=timezone.now().date()
                    ).count(),
                    'this_week': User.objects.filter(
                        date_joined__gte=timezone.now() - timedelta(days=7)
                    ).count(),
                    'this_month': new_users_30d,
                }
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"❌ Failed to get user statistics: {e}")
            return Response({
                'error': 'Failed to get user statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search users by username, email, or other criteria"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'Search query required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )[:50]  # Limit results
            
            serializer = self.get_serializer(users, many=True)
            return Response({
                'query': query,
                'results': serializer.data,
                'count': len(serializer.data)
            })
            
        except Exception as e:
            logger.error(f"❌ User search failed: {e}")
            return Response({
                'error': 'Search failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIKeyAdminViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for API key management (staff only).
    """
    queryset = APIKey.objects.all().order_by('-created_at')
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get API key statistics for admin dashboard"""
        try:
            # Total counts
            total_keys = APIKey.objects.count()
            active_keys = APIKey.objects.filter(is_active=True).count()
            validated_keys = APIKey.objects.filter(is_validated=True).count()
            
            # Exchange distribution
            exchange_stats = APIKey.objects.values('exchange').annotate(
                count=Count('id'),
                active_count=Count('id', filter=Q(is_active=True)),
                validated_count=Count('id', filter=Q(is_validated=True))
            )
            
            # Recent activity
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_keys = APIKey.objects.filter(
                created_at__gte=thirty_days_ago
            ).count()
            
            # Validation status
            validation_stats = {
                'validated': validated_keys,
                'not_validated': active_keys - validated_keys,
                'inactive': total_keys - active_keys
            }
            
            stats = {
                'total_keys': total_keys,
                'active_keys': active_keys,
                'validated_keys': validated_keys,
                'validation_rate': round((validated_keys / active_keys * 100) if active_keys > 0 else 0, 1),
                'exchange_distribution': list(exchange_stats),
                'recent_activity': recent_keys,
                'validation_status': validation_stats,
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"❌ Failed to get API key statistics: {e}")
            return Response({
                'error': 'Failed to get API key statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def bulk_validate(self, request):
        """Bulk validate all API keys (admin only)"""
        try:
            # Get all API keys
            api_keys = APIKey.objects.filter(is_active=True)
            results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'details': []
            }
            
            for api_key in api_keys:
                try:
                    from ..services.security_service import SecurityService
                    result = SecurityService.test_api_key_connection(api_key, force_test=True)
                    
                    if result.get('connected', False):
                        api_key.mark_as_validated(True)
                        results['successful'] += 1
                        results['details'].append({
                            'api_key_id': api_key.id,
                            'exchange': api_key.exchange,
                            'user': api_key.user.username,
                            'status': 'validated'
                        })
                    else:
                        api_key.mark_as_validated(False)
                        results['failed'] += 1
                        results['details'].append({
                            'api_key_id': api_key.id,
                            'exchange': api_key.exchange,
                            'user': api_key.user.username,
                            'status': 'failed',
                            'error': result.get('error')
                        })
                    
                    results['total_processed'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['details'].append({
                        'api_key_id': api_key.id,
                        'exchange': api_key.exchange,
                        'user': api_key.user.username,
                        'status': 'error',
                        'error': str(e)
                    })
                    results['total_processed'] += 1
            
            logger.info(f"✅ Admin bulk validation completed: {results['successful']} successful, {results['failed']} failed")
            
            return Response(results)
            
        except Exception as e:
            logger.error(f"❌ Admin bulk validation failed: {e}")
            return Response({
                'error': f'Bulk validation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminDashboardView(APIView):
    """
    Comprehensive admin dashboard.
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get admin dashboard data"""
        try:
            # User statistics
            user_stats = User.objects.aggregate(
                total_users=Count('id'),
                active_users=Count('id', filter=Q(is_active=True)),
                new_today=Count('id', filter=Q(date_joined__date=timezone.now().date())),
                new_week=Count('id', filter=Q(date_joined__gte=timezone.now() - timedelta(days=7)))
            )
            
            # API key statistics
            api_key_stats = APIKey.objects.aggregate(
                total_keys=Count('id'),
                active_keys=Count('id', filter=Q(is_active=True)),
                validated_keys=Count('id', filter=Q(is_validated=True))
            )
            
            # Recent activity
            recent_users = User.objects.order_by('-date_joined')[:5]
            recent_api_keys = APIKey.objects.order_by('-created_at')[:5]
            
            dashboard_data = {
                'user_statistics': user_stats,
                'api_key_statistics': api_key_stats,
                'recent_activity': {
                    'users': UserSerializer(recent_users, many=True).data,
                    'api_keys': APIKeySerializer(recent_api_keys, many=True).data,
                },
                'system_health': {
                    'database': 'healthy',
                    'cache': 'healthy',
                    'exchanges': 'monitoring',
                    'last_updated': timezone.now().isoformat()
                }
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            logger.error(f"❌ Admin dashboard failed: {e}")
            return Response({
                'error': 'Failed to load admin dashboard'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)