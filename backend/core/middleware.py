# backend/core/middleware.py

import time
import json
import base64
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and responses.
    """
    
    def process_request(self, request):
        """
        Log incoming request.
        """
        request.start_time = time.time()
        
        # Skip logging for health checks or static files
        if self._should_skip_logging(request):
            return None
            
        # Get username safely from request.user or Authorization header JWT
        username = getattr(request, 'user', None)
        if username and getattr(username, 'is_authenticated', False):
            username = username.username
            # include id for clarity
            username_log = f"{username} (id:{getattr(request.user, 'id', 'n/a')})"
        else:
            # try to infer from Authorization header
            inferred = self._get_username_from_authorization(request)
            username_log = inferred or 'Anonymous'
            
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {self._get_client_ip(request)} "
            f"User: {username_log}"
        )
        
        # Log request body for non-GET requests (be careful with sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.body:
            try:
                body = json.loads(request.body.decode('utf-8'))
                # Mask sensitive fields
                masked_body = self._mask_sensitive_data(body)
                logger.debug(f"Request body: {masked_body}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.debug("Request body: (non-JSON or binary data)")

    def _get_username_from_authorization(self, request):
        """
        Try to decode JWT from Authorization header (without verification) to extract username/email.
        If only user_id is present, attempt a lightweight DB lookup to resolve username.
        This is only for logging — do not rely on this for auth.
        """
        auth = request.META.get('HTTP_AUTHORIZATION', '') or request.headers.get('Authorization', '')
        if not auth:
            return None
        parts = auth.split()
        if len(parts) != 2:
            return None
        scheme, token = parts
        if scheme.lower() != 'bearer':
            return None
        try:
            # JWT format header.payload.signature
            payload_b64 = token.split('.')[1]
            padding = '=' * (-len(payload_b64) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
            payload = json.loads(payload_bytes.decode('utf-8'))
        except Exception:
            return None

        # Prefer explicit username/email claims
        username = payload.get('username') or payload.get('preferred_username') or payload.get('email')
        if username:
            # include id if present
            uid = payload.get('user_id') or payload.get('sub')
            return f"{username}{f' (id:{uid})' if uid else ''}"

        # If only user_id present, attempt a fast DB lookup to resolve username
        user_id = payload.get('user_id') or payload.get('sub')
        if user_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.filter(id=user_id).values('username').first()
                if user and user.get('username'):
                    return f"{user['username']} (id:{user_id})"
                return f"user_id:{user_id}"
            except Exception:
                # On any error, fall back to showing raw id
                return f"user_id:{user_id}"

        return None

    def _mask_sensitive_data(self, body):
        """
        Mask common sensitive fields before logging.
        """
        if not isinstance(body, dict):
            return body
        masked = {}
        sensitive_keys = {'password', 'api_key', 'secret_key', 'token', 'refresh_token', 'passphrase'}
        for k, v in body.items():
            if k.lower() in sensitive_keys:
                masked[k] = '***REDACTED***'
            else:
                try:
                    masked[k] = v if not isinstance(v, dict) else self._mask_sensitive_data(v)
                except Exception:
                    masked[k] = '***UNSERIALIZABLE***'
        return masked

    def _get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _should_skip_logging(self, request):
        """
        Determine if logging should be skipped for this request.
        """
        skip_paths = ['/health/', '/static/', '/media/', '/favicon.ico']
        return any(request.path.startswith(path) for path in skip_paths)
    
    def process_response(self, request, response):
        """
        Log response and calculate request duration.
        """
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            if not self._should_skip_logging(request):
                logger.info(
                    f"Response: {request.method} {request.path} "
                    f"Status: {response.status_code} "
                    f"Duration: {duration:.3f}s"
                )
        
        return response
    
    def process_exception(self, request, exception):
        """
        Log exceptions and handle uncaught ones.
        """
        logger.error(
            f"Exception in {request.method} {request.path}: {exception}",
            exc_info=True
        )
        
        # Let the custom exception handler deal with it
        return None
    
    def _should_skip_rate_limit(self, request):
        """
        Determine if rate limiting should be skipped for this request.
        """
        skip_paths = ['/health/', '/static/', '/media/']
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _clean_old_entries(self, current_time):
        """
        Clean request entries older than 1 minute.
        """
        cutoff_time = current_time - 60  # 1 minute
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff_time]
            if not self.requests[ip]:
                del self.requests[ip]

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    
    def process_response(self, request, response):
        """
        Add security headers to response.
        """
        # Content Security Policy
        response['Content-Security-Policy'] = "default-src 'self'"
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Strict-Transport-Security (only in production)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer-Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """
    Basic rate limiting middleware.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.requests = {}
    
    def process_request(self, request):
        """
        Check rate limit for the client.
        """
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request):
            return None
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._clean_old_entries(current_time)
        
        # Check rate limit
        if client_ip in self.requests:
            request_times = self.requests[client_ip]
            # Allow 100 requests per minute
            if len(request_times) >= 100:
                return JsonResponse({
                    'error': {
                        'code': 'rate_limit_exceeded',
                        'message': 'Rate limit exceeded. Please try again later.',
                        'type': 'RateLimitExceeded'
                    }
                }, status=429)
            
            request_times.append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        return None
    
    def _get_client_ip(self, request):
        """
        Get client IP address.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def _should_skip_rate_limit(self, request):
        """
        Determine if rate limiting should be skipped for this request.
        """
        skip_paths = ['/health/', '/static/', '/media/']
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _clean_old_entries(self, current_time):
        """
        Clean request entries older than 1 minute.
        """
        cutoff_time = current_time - 60  # 1 minute
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff_time]
            if not self.requests[ip]:
                del self.requests[ip]