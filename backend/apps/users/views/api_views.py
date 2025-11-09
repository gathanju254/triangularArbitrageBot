# backend/apps/users/views/api_views.py
import logging
from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.core.cache import cache

from ..models import User, UserProfile, APIKey
from ..serializers import (
    UserSerializer, UserUpdateSerializer, UserDashboardSerializer,
    APIKeySerializer, APIKeyCreateSerializer, APIKeyDetailSerializer,
    APIKeyUpdateSerializer, APIKeyTestSerializer, APIKeyExportSerializer,
    APIKeyRotationSerializer, APIKeySummarySerializer, APIKeyValidationResultSerializer,
    ChangePasswordSerializer, APIKeyBulkOperationSerializer
)
from ..services.api_key_service import APIKeyService
from ..services.user_service import UserService
from ..services.security_service import SecurityService

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_api_keys(request):
    """Get all API keys for the current user"""
    try:
        api_keys = APIKey.objects.filter(user=request.user).order_by('-created_at')
        
        # Format the response to match frontend expectations
        keys_data = []
        for key in api_keys:
            keys_data.append({
                'id': key.id,
                'exchange': key.exchange,
                'label': key.label,
                'api_key': key.api_key,  # This will be encrypted in the database
                'secret_key': key.secret_key,  # This will be encrypted in the database
                'passphrase': key.passphrase,
                'is_active': key.is_active,
                'is_validated': key.is_validated,
                'created_at': key.created_at.isoformat() if key.created_at else None,
                'last_used': key.last_used.isoformat() if key.last_used else None,
            })
        
        return Response({
            'api_keys': keys_data,
            'count': len(keys_data)
        })
        
    except Exception as e:
        return Response({
            'error': str(e),
            'api_keys': []  # Always return empty array on error
        }, status=500)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management operations.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'update':
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        # Users can only access their own data
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update user profile"""
        serializer = UserUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user statistics"""
        try:
            stats = UserService.get_user_stats(request.user)
            return Response(stats)
        except Exception as e:
            logger.error(f"Failed to get user statistics: {e}")
            return Response(
                {'error': 'Failed to get user statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class APIKeyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for comprehensive API key management.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return APIKeyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return APIKeyUpdateSerializer
        elif self.action == 'list':
            return APIKeySummarySerializer
        return APIKeyDetailSerializer
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create API key using service layer"""
        logger.info(f"🔑 Creating API key for user: {self.request.user.username}")
        serializer.save()
    
    def perform_update(self, serializer):
        """Update API key using service layer"""
        instance = self.get_object()
        logger.info(f"🔄 Updating API key: {instance.id}")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Delete API key with cache cleanup"""
        logger.info(f"🗑️ Deleting API key: {instance.id}")
        instance.delete()
        
        # Clear relevant caches - use local method instead of APIKeyManager
        self._clear_credentials_cache(instance.user)
    
    def _clear_credentials_cache(self, user):
        """Clear credentials cache for user"""
        try:
            cache_keys = [
                f"apikey_service:user_{user.id}_active",
                f"apikey_service:user_{user.id}_all", 
                f"apikey_service:user_{user.id}_trading",
                f"apikey_service:user_{user.id}_stats",
            ]
            cache.delete_many(cache_keys)
        except Exception as e:
            logger.debug(f"Cache clearance error: {e}")
    
    def list(self, request, *args, **kwargs):
        """List API keys with enhanced response - FIXED for frontend compatibility"""
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            # Add statistics to response
            stats = APIKeyService.get_user_api_key_stats(request.user)
            health = self._get_api_key_health(request.user)
            
            # Return consistent structure that frontend expects
            response_data = {
                'api_keys': serializer.data,  # This is the main array of API keys
                'statistics': stats,
                'health_status': health,
                'count': len(serializer.data)
            }
            
            logger.info(f"✅ API keys list response prepared with {len(serializer.data)} keys")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"❌ API keys list error: {e}")
            # Return empty array structure to prevent frontend errors
            return Response({
                'api_keys': [],
                'statistics': {},
                'health_status': {},
                'count': 0,
                'error': 'Failed to load API keys'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_api_key_health(self, user):
        """Get API key health status"""
        try:
            api_keys = APIKey.objects.filter(user=user, is_active=True)
            total = api_keys.count()
            validated = api_keys.filter(is_validated=True).count()
            
            return {
                'healthy': validated > 0,
                'total_keys': total,
                'validated_keys': validated,
                'validation_rate': round((validated / total * 100) if total > 0 else 0, 1),
                'status': 'healthy' if validated > 0 else 'needs_attention'
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'healthy': False,
                'total_keys': 0,
                'validated_keys': 0,
                'validation_rate': 0,
                'status': 'error'
            }
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test API key connection"""
        api_key = self.get_object()
        
        serializer = APIKeyTestSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        force_test = serializer.validated_data.get('force_test', False)
        
        try:
            result = SecurityService.test_api_key_connection(api_key, force_test=force_test)
            response_serializer = APIKeyValidationResultSerializer(result)
            
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"❌ API key test failed: {e}")
            return Response(
                {'error': f'Test failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def health_check(self, request):
        """Comprehensive health check for all API keys"""
        health = self._get_api_key_health(request.user)
        return Response(health)
    
    @action(detail=False, methods=['post'])
    def bulk_validate(self, request):
        """Bulk validate all API keys"""
        results = self._bulk_validate_and_update(request.user)
        return Response(results)
    
    def _bulk_validate_and_update(self, user):
        """Bulk validate and update API keys"""
        try:
            api_keys = APIKey.objects.filter(user=user, is_active=True)
            results = {
                'total': api_keys.count(),
                'validated': 0,
                'failed': 0,
                'details': []
            }
            
            for api_key in api_keys:
                try:
                    result = SecurityService.test_api_key_connection(api_key, force_test=True)
                    if result.get('connected', False):
                        api_key.mark_as_validated(True)
                        results['validated'] += 1
                        status_msg = 'validated'
                    else:
                        api_key.mark_as_validated(False)
                        results['failed'] += 1
                        status_msg = 'failed'
                    
                    results['details'].append({
                        'api_key_id': api_key.id,
                        'exchange': api_key.exchange,
                        'status': status_msg,
                        'error': result.get('error')
                    })
                    
                except Exception as e:
                    results['failed'] += 1
                    results['details'].append({
                        'api_key_id': api_key.id,
                        'exchange': api_key.exchange,
                        'status': 'error',
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk validation error: {e}")
            return {
                'total': 0,
                'validated': 0,
                'failed': 0,
                'error': str(e)
            }
    
    @action(detail=False, methods=['get'])
    def usage_statistics(self, request):
        """Get API key usage statistics"""
        stats = self._get_usage_statistics(request.user)
        return Response(stats)
    
    def _get_usage_statistics(self, user):
        """Get usage statistics for user's API keys"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            api_keys = APIKey.objects.filter(user=user)
            total = api_keys.count()
            active = api_keys.filter(is_active=True).count()
            validated = api_keys.filter(is_active=True, is_validated=True).count()
            
            # Recent activity (last 7 days)
            week_ago = timezone.now() - timedelta(days=7)
            recent_usage = api_keys.filter(last_used__gte=week_ago).count()
            
            return {
                'total_keys': total,
                'active_keys': active,
                'validated_keys': validated,
                'recent_activity': recent_usage,
                'validation_rate': round((validated / active * 100) if active > 0 else 0, 1)
            }
        except Exception as e:
            logger.error(f"Usage statistics error: {e}")
            return {
                'total_keys': 0,
                'active_keys': 0,
                'validated_keys': 0,
                'recent_activity': 0,
                'validation_rate': 0
            }


class ChangePasswordView(generics.UpdateAPIView):
    """
    Change user password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        logger.info(f"🔐 Password change attempt for user: {user.username}")
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                logger.warning(f"❌ Password change failed: Incorrect current password for {user.username}")
                return Response({
                    'old_password': ['Current password is incorrect']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            logger.info(f"✅ Password changed successfully for user: {user.username}")
            
            return Response({
                'message': 'Password updated successfully'
            })
        
        logger.warning(f"❌ Password change validation failed for {user.username}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class APIKeyBulkOperationsView(APIView):
    """
    Perform bulk operations on API keys.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = APIKeyBulkOperationSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        operations = serializer.validated_data['operations']
        
        logger.info(f"🔄 Performing {len(operations)} bulk operations on API keys")
        
        # Use the service for bulk operations
        results = APIKeyService.bulk_operations(request.user, operations)
        
        logger.info(f"✅ Bulk operations completed: {results['successful']} successful, {results['failed']} failed")
        
        return Response(results)


class APIKeyExportView(generics.ListAPIView):
    """
    Export API key data (without sensitive information).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = APIKeyExportSerializer
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user).order_by('exchange')
    
    def list(self, request, *args, **kwargs):
        """Export API key data"""
        logger.info(f"📤 Exporting API keys for user: {request.user.username}")
        
        response = super().list(request, *args, **kwargs)
        
        # Add export metadata
        response.data = {
            'exported_at': timezone.now().isoformat(),
            'user': request.user.username,
            'total_keys': len(response.data),
            'api_keys': response.data
        }
        
        return response


class APIKeyRotationView(APIView):
    """
    Rotate encryption for all user API keys.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = APIKeyRotationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🔄 Starting encryption rotation for user: {request.user.username}")
        
        try:
            # Use service for encryption rotation
            results = SecurityService.rotate_encryption_for_user(request.user)
            
            if results['failed'] > 0:
                logger.warning(f"⚠️ Encryption rotation completed with {results['failed']} failures")
                return Response({
                    'message': f"Encryption rotation completed with {results['failed']} failures",
                    'results': results
                }, status=status.HTTP_207_MULTI_STATUS)
            else:
                logger.info(f"✅ Encryption rotation completed successfully")
                return Response({
                    'message': 'Encryption rotation completed successfully',
                    'results': results
                })
                
        except Exception as e:
            logger.error(f"❌ Encryption rotation failed: {e}")
            return Response({
                'error': f'Encryption rotation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDashboardView(APIView):
    """
    Get comprehensive dashboard data for the user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        logger.info(f"📊 Generating dashboard for user: {request.user.username}")
        
        try:
            # Get user data
            user_serializer = UserDashboardSerializer(request.user)
            
            # Get API key statistics and health
            api_key_stats = APIKeyService.get_user_api_key_stats(request.user)
            api_key_health = self._get_api_key_health(request.user)
            
            # Get recent API keys
            recent_api_keys = APIKey.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
            
            recent_api_keys_serializer = APIKeySummarySerializer(recent_api_keys, many=True)
            
            # Get usage statistics
            usage_stats = self._get_usage_statistics(request.user)
            
            dashboard_data = {
                'user': user_serializer.data,
                'api_key_statistics': api_key_stats,
                'api_key_health': api_key_health,
                'recent_api_keys': recent_api_keys_serializer.data,
                'usage_statistics': usage_stats,
                'system_status': {
                    'trading_engine': 'operational',
                    'exchange_connections': 'operational' if api_key_health['healthy'] else 'degraded',
                    'last_updated': timezone.now().isoformat()
                }
            }
            
            logger.info(f"✅ Dashboard generated successfully for {request.user.username}")
            
            return Response(dashboard_data)
            
        except Exception as e:
            logger.error(f"❌ Dashboard generation failed: {e}")
            return Response({
                'error': 'Failed to generate dashboard data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_api_key_health(self, user):
        """Get API key health status for dashboard"""
        try:
            api_keys = APIKey.objects.filter(user=user, is_active=True)
            total = api_keys.count()
            validated = api_keys.filter(is_validated=True).count()
            
            return {
                'healthy': validated > 0,
                'total_keys': total,
                'validated_keys': validated,
                'validation_rate': round((validated / total * 100) if total > 0 else 0, 1),
                'status': 'healthy' if validated > 0 else 'needs_attention'
            }
        except Exception as e:
            logger.error(f"Dashboard health check error: {e}")
            return {
                'healthy': False,
                'total_keys': 0,
                'validated_keys': 0,
                'validation_rate': 0,
                'status': 'error'
            }
    
    def _get_usage_statistics(self, user):
        """Get usage statistics for dashboard"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            api_keys = APIKey.objects.filter(user=user)
            total = api_keys.count()
            active = api_keys.filter(is_active=True).count()
            validated = api_keys.filter(is_active=True, is_validated=True).count()
            
            # Recent activity (last 7 days)
            week_ago = timezone.now() - timedelta(days=7)
            recent_usage = api_keys.filter(last_used__gte=week_ago).count()
            
            return {
                'total_keys': total,
                'active_keys': active,
                'validated_keys': validated,
                'recent_activity': recent_usage,
                'validation_rate': round((validated / active * 100) if active > 0 else 0, 1)
            }
        except Exception as e:
            logger.error(f"Dashboard usage statistics error: {e}")
            return {
                'total_keys': 0,
                'active_keys': 0,
                'validated_keys': 0,
                'recent_activity': 0,
                'validation_rate': 0
            }