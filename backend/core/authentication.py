# backend/core/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt

User = get_user_model()

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that includes user validation and additional security checks.
    """
    
    def authenticate(self, request):
        """
        Override to add custom validation and user status checks.
        """
        try:
            # Get the token from the header
            header = self.get_header(request)
            if header is None:
                return None

            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

            # Validate token
            validated_token = self.get_validated_token(raw_token)
            
            # Get user from token
            user = self.get_user(validated_token)
            
            # Additional security checks
            self._validate_user_status(user)
            self._validate_token_issuer(validated_token)
            
            return (user, validated_token)
            
        except InvalidToken:
            raise AuthenticationFailed(_('Invalid token.'))
        except User.DoesNotExist:
            raise AuthenticationFailed(_('User not found.'))
        except Exception as e:
            raise AuthenticationFailed(_('Authentication failed.'))

    def _validate_user_status(self, user):
        """
        Validate that the user is active and verified (if required).
        """
        if not user.is_active:
            raise AuthenticationFailed(_('User account is disabled.'))
        
        # Optional: Check if user email is verified
        if getattr(settings, 'REQUIRE_EMAIL_VERIFICATION', False) and not user.is_verified:
            raise AuthenticationFailed(_('Email verification required.'))

    def _validate_token_issuer(self, token):
        """
        Validate token issuer if configured.
        """
        issuer = getattr(settings, 'JWT_ISSUER', None)
        if issuer and token.get('iss') != issuer:
            raise InvalidToken(_('Invalid token issuer.'))

class APIKeyAuthentication:
    """
    Authentication for exchange API keys (for internal service communication).
    """
    keyword = 'APIKey'
    
    def authenticate(self, request):
        """
        Authenticate using API key from header.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith(f'{self.keyword} '):
            return None
            
        try:
            api_key = auth_header.split(' ')[1]
            # Validate API key (you might want to store service API keys in settings or database)
            if api_key == getattr(settings, 'SERVICE_API_KEY', ''):
                # Return a service user or None for service-level authentication
                return (None, api_key)
        except (IndexError, AttributeError):
            pass
            
        return None

    def authenticate_header(self, request):
        """
        Return the authentication header.
        """
        return self.keyword

class WebSocketJWTAuthentication:
    """
    JWT authentication for WebSocket connections.
    """
    
    def __init__(self):
        self.jwt_authentication = CustomJWTAuthentication()
    
    def authenticate(self, scope):
        """
        Authenticate WebSocket connection using JWT token from query string.
        """
        try:
            # Extract token from query string
            query_string = scope.get('query_string', b'').decode()
            token = None
            
            # Parse query string for token
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param[6:]  # Remove 'token='
                    break
            
            if not token:
                return None
            
            # Create a mock request for JWT authentication
            class MockRequest:
                def __init__(self, token):
                    self.META = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
            
            mock_request = MockRequest(token)
            return self.jwt_authentication.authenticate(mock_request)
            
        except Exception:
            return None