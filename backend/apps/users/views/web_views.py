# backend/apps/users/views/web_views.py
import logging
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
try:
    from rest_framework_simplejwt.tokens import RefreshToken
except Exception:
    class _MissingRefreshToken:
        @staticmethod
        def for_user(user):
            raise RuntimeError(
                "rest_framework_simplejwt.tokens.RefreshToken is not available; "
                "please install 'djangorestframework-simplejwt' to enable JWT token operations."
            )
    RefreshToken = _MissingRefreshToken()
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from ..models import User
from ..serializers import (
    UserRegistrationSerializer, UserSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer,
    ExchangeCredentialsSerializer
)
from ..services.user_service import UserService
from apps.exchanges.services import ExchangeService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """
    Register a new user account.
    
    Creates a new user with profile and returns JWT tokens.
    """
    logger.info("🔧 User registration attempt", extra={
        'username': request.data.get('username'),
        'email': request.data.get('email')
    })
    
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        logger.info("✅ Registration data validation passed")
        
        try:
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            logger.info(f"✅ User registered successfully: {user.username}")
            
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Account created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ User registration failed: {e}")
            return Response({
                'error': 'Failed to create user account',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        logger.warning("❌ Registration validation failed", extra={
            'errors': serializer.errors
        })
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """
    Authenticate user and return JWT tokens.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    logger.info(f"🔧 Login attempt for user: {username}")
    
    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if user is not None:
        if not user.is_active:
            logger.warning(f"❌ Login failed: User {username} is inactive")
            return Response({
                'error': 'Account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"✅ User logged in successfully: {user.username}")
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful'
        })
    else:
        logger.warning(f"❌ Login failed: Invalid credentials for user {username}")
        return Response({
            'error': 'Invalid username or password'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """
    Logout user by blacklisting refresh token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        # fallback: allow clients to send refresh token via Authorization header (rare)
        if not refresh_token:
            auth = request.META.get('HTTP_AUTHORIZATION', '') or request.headers.get('Authorization', '')
            if auth and auth.startswith('Bearer '):
                candidate = auth.split(' ', 1)[1].strip()
                refresh_token = candidate

        if not refresh_token:
            # best-effort: nothing to blacklist, but respond OK to complete logout
            logger.info(f"✅ User logout requested (no refresh token) by user: {getattr(request.user, 'username', 'Unknown')}")
            return Response({'message': 'Logged out (no refresh token provided)'}, status=status.HTTP_200_OK)

        token = RefreshToken(refresh_token)
        token.blacklist()

        logger.info(f"✅ User logged out: {request.user.username}")
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Logout failed: {e}")
        return Response({'error': 'Invalid token or logout failed'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password_request(request):
    """
    Request a password reset.
    """
    serializer = PasswordResetSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # In production: Generate reset token, send email, store token
            logger.info(f"📧 Password reset requested for user: {user.username}")
            
            return Response({
                'message': 'If an account with this email exists, reset instructions have been sent',
                'email': email  # Remove this in production
            })
            
        except User.DoesNotExist:
            # Don't reveal whether email exists for security
            logger.info(f"📧 Password reset requested for non-existent email: {email}")
            return Response({
                'message': 'If an account with this email exists, reset instructions have been sent'
            })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password_confirm(request):
    """
    Confirm password reset with token.
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        # In production: Validate token, update password, invalidate token
        logger.info("✅ Password reset confirmed")
        
        return Response({
            'message': 'Password has been reset successfully'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def validate_exchange_credentials(request):
    """
    Validate exchange credentials without saving them.
    """
    serializer = ExchangeCredentialsSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    exchange = serializer.validated_data['exchange']
    api_key = serializer.validated_data['api_key']
    secret_key = serializer.validated_data['secret_key']
    passphrase = serializer.validated_data.get('passphrase')
    
    logger.info(f"🔍 Validating exchange credentials for {exchange}")
    
    try:
        # Test connection
        exchange_service = ExchangeService()
        result = exchange_service.test_connection(
            exchange=exchange,
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase
        )
        
        logger.info(f"✅ Exchange credentials validation completed for {exchange}")
        
        return Response({
            'valid': result.get('connected', False),
            'exchange': exchange,
            'permissions': result.get('permissions', []),
            'account_type': result.get('account_type', 'unknown'),
            'error': result.get('error'),
            'timestamp': timezone.now().isoformat()
        })
        
    except ImportError:
        logger.error("Exchange service not available for credentials validation")
        return Response({
            'error': 'Exchange service not available',
            'valid': False
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"❌ Exchange credentials validation failed: {e}")
        return Response({
            'error': f'Validation failed: {str(e)}',
            'valid': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Django Template Views (for web interface)
@login_required
def profile_view(request):
    """User profile page"""
    return render(request, 'users/profile.html', {
        'user': request.user
    })


@login_required
def api_keys_view(request):
    """API keys management page"""
    return render(request, 'users/api_keys.html', {
        'user': request.user
    })


@login_required
def dashboard_view(request):
    """User dashboard page"""
    return render(request, 'users/dashboard.html', {
        'user': request.user
    })