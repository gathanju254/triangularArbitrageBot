# backend/tudollar_backend/settings/development.py

from .base import *
import os
from cryptography.fernet import Fernet
import base64
from datetime import timedelta

# Debug settings
DEBUG = True

# Database - Using SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Additional development apps
INSTALLED_APPS += [
    'debug_toolbar',  # Optional: for debugging
]

# Middleware for development
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Debug toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# =====================================
# REDIS & CELERY CONFIGURATION - MEMORY BACKEND
# =====================================
# Redis configuration - Use memory backend for development
REDIS_URL = os.environ.get('REDIS_URL', 'memory://')

# Celery Configuration for memory backend
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_POOL = 'solo'  # Use solo pool for Windows compatibility
CELERY_WORKER_CONCURRENCY = 1  # Single worker process for Windows

# Optional: Enable Celery Beat in development if needed
ENABLE_CELERY_BEAT = os.environ.get('ENABLE_CELERY_BEAT', 'false').lower() == 'true'

# Execute Celery tasks locally (no broker required) in development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =====================================
# ENCRYPTION SETTINGS
# =====================================
# Get encryption key from environment or use a development default
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    # Generate a development key if not set in environment
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print("⚠️  Using auto-generated encryption key for development")
else:
    # Ensure the key from environment is properly formatted
    try:
        # Test if the key is valid for Fernet
        Fernet(ENCRYPTION_KEY.encode())
        print("✅ Using environment encryption key")
    except Exception as e:
        print(f"❌ Invalid encryption key from environment: {e}")
        # Fallback to generated key
        ENCRYPTION_KEY = Fernet.generate_key().decode()
        print("⚠️  Falling back to auto-generated encryption key")

# REST Framework settings for development
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Enable browsable API in development
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

# Allow some endpoints to be public
REST_FRAMEWORK_EXCEPTIONS = {
    'EXCLUDE_FROM_AUTH': [
        '/api/users/login/',
        '/api/users/register/',
        '/api/users/token/refresh/',
        '/api/users/reset-password/',
        '/api/users/password-reset/confirm/',
        '/api/health/',
    ]
}

# JWT Settings for development
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),  # Longer tokens for development
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# =====================================
# CORS SETTINGS FOR DEVELOPMENT
# =====================================
# In development.py - ensure this exists:
CORS_ALLOW_ALL_ORIGINS = True  # Allow all in development
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Security settings for development (less restrictive)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Cache settings for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,  # 1/3 of entries removed when max reached
        }
    }
}

import django.core.cache
cache_info = f"Cache Backend: {django.core.cache.cache.__class__.__name__}"
print(f"🔧 {cache_info}")

# File upload settings for development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files settings for development
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Development-specific app settings
TRADING_ENABLED = True
REQUIRE_EMAIL_VERIFICATION = False  # Disable email verification in development
ALLOW_DEMO_TRADING = True

# Exchange API settings for development
EXCHANGE_SETTINGS = {
    'BINANCE': {
        'TESTNET': True,  # Use Binance testnet in development
    },
    'OKX': {
        'DEMO': True,  # Use OKX demo mode in development
    }
}

# Debug logging for API keys and encryption
API_KEY_DEBUG = True

# Print important settings on startup
print("🔧 Development Settings Loaded:")
print(f"   DEBUG: {DEBUG}")
print(f"   DATABASE: {DATABASES['default']['ENGINE']}")
print(f"   ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"   CORS_ALLOW_ALL_ORIGINS: {CORS_ALLOW_ALL_ORIGINS}")
print(f"   CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")
print(f"   TRADING_ENABLED: {TRADING_ENABLED}")
print(f"   ENCRYPTION_KEY: {'***' + ENCRYPTION_KEY[-8:] if ENCRYPTION_KEY else 'Not set'}")
print(f"   REDIS_URL: {REDIS_URL}")
print(f"   CELERY_BROKER_URL: {CELERY_BROKER_URL}")
print(f"   CELERY_RESULT_BACKEND: {CELERY_RESULT_BACKEND}")
print(f"   CELERY_TASK_ALWAYS_EAGER: {CELERY_TASK_ALWAYS_EAGER}")
print(f"   ENABLE_CELERY_BEAT: {ENABLE_CELERY_BEAT}")