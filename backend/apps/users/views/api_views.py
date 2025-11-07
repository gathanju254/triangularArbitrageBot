# backend/apps/users/views/api_views.py
import logging
from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import action
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
from apps.exchanges.api_key_manager import APIKeyManager

logger = logging.getLogger(__name__)


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
        
        # Clear relevant caches
        APIKeyManager.rotate_credentials_cache(instance.user)
    
    def list(self, request, *args, **kwargs):
        """List API keys with enhanced response"""
        response = super().list(request, *args, **kwargs)
        
        # Add statistics to response
        stats = APIKeyService.get_user_api_key_stats(request.user)
        health = APIKeyManager.health_check(request.user)
        
        response.data = {
            'api_keys': response.data,
            'statistics': stats,
            'health_status': health,
            'count': len(response.data)
        }
        
        return response
    
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
        health = APIKeyManager.health_check(request.user)
        return Response(health)
    
    @action(detail=False, methods=['post'])
    def bulk_validate(self, request):
        """Bulk validate all API keys"""
        results = APIKeyManager.bulk_validate_and_update(request.user)
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def usage_statistics(self, request):
        """Get API key usage statistics"""
        stats = APIKeyManager.get_usage_statistics(request.user)
        return Response(stats)


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
            api_key_health = APIKeyManager.health_check(request.user)
            
            # Get recent API keys
            recent_api_keys = APIKey.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
            
            recent_api_keys_serializer = APIKeySummarySerializer(recent_api_keys, many=True)
            
            # Get usage statistics
            usage_stats = APIKeyManager.get_usage_statistics(request.user)
            
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