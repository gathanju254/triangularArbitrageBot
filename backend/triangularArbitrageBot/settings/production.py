# backend/tudollar_backend/settings/production.py

from .base import *
import os
import dj_database_url
from datetime import timedelta

# =====================================
# SECURITY SETTINGS
# =====================================
DEBUG = False
ALLOWED_HOSTS = os.getenv('RENDER_EXTERNAL_HOSTNAME', '').split(',') + [
    'tudollar-backend.onrender.com',
    'localhost',
    '127.0.0.1'
]

# =====================================
# DATABASE CONFIGURATION (PostgreSQL)
# =====================================
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if not os.getenv('DATABASE_URL'):
    print("⚠️  WARNING: DATABASE_URL not set, using SQLite fallback")
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# =====================================
# SECURITY HEADERS
# =====================================
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =====================================
# STATIC FILES
# =====================================
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Insert WhiteNoise middleware after SecurityMiddleware
whitenoise_index = None
for i, middleware in enumerate(MIDDLEWARE):
    if 'SecurityMiddleware' in middleware:
        whitenoise_index = i + 1
        break
if whitenoise_index is not None:
    MIDDLEWARE.insert(whitenoise_index, 'whitenoise.middleware.WhiteNoiseMiddleware')
else:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# =====================================
# REDIS CONFIGURATION
# =====================================
# Get Redis URL from environment - Render should provide this automatically
REDIS_URL = os.environ.get("REDIS_URL")

if not REDIS_URL:
    print("❌ REDIS_URL not found in environment variables!")
    print("⚠️  Please set REDIS_URL in your Render environment variables")
    print("⚠️  Celery and background tasks will not work without Redis")
    # Don't set a fallback - let it fail clearly
    REDIS_URL = None
else:
    print(f"✅ Redis configured: {REDIS_URL.split('@')[-1] if '@' in REDIS_URL else REDIS_URL}")

# =====================================
# CELERY CONFIGURATION
# =====================================
# Improved Celery configuration with better Redis connection handling
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Enhanced Redis connection settings
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 3
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_HEARTBEAT = 0
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,  # 1 hour
    'socket_connect_timeout': 5,
    'socket_keepalive': True,
    'retry_on_timeout': True,
    'max_connections': 20,
}

# Celery task configuration
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_IGNORE_RESULT = False

# Task routes for different queues
CELERY_TASK_ROUTES = {
    'apps.risk_management.tasks.*': {'queue': 'risk'},
    'apps.arbitrage.tasks.*': {'queue': 'trading'},
    'apps.exchanges.tasks.*': {'queue': 'data'},
    'apps.analytics.tasks.*': {'queue': 'analytics'},
    'apps.users.tasks.*': {'queue': 'users'},
    'apps.notifications.tasks.*': {'queue': 'notifications'},
    'apps.trading.tasks.*': {'queue': 'trading'},
}

# Only configure Redis-based services if Redis is available
if REDIS_URL:
    # Use the environment Redis URL directly
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
                "socket_connect_timeout": 5,
                "socket_keepalive": True,
            },
        },
    }
    
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 20,
                    "retry_on_timeout": True,
                },
            },
        }
    }
else:
    print("⚠️  Redis not configured - using memory backend and disabling Celery async tasks")
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_TASK_ALWAYS_EAGER = True
    
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# =====================================
# REDIS CONNECTION TESTING
# =====================================
# Test Redis connection on startup
if REDIS_URL:
    try:
        import redis
        print("🔍 Testing Redis connection...")
        r = redis.from_url(
            REDIS_URL, 
            socket_connect_timeout=5,
            socket_keepalive=True,
            retry_on_timeout=True,
            max_connections=10
        )
        r.ping()
        print("✅ Redis connection test: SUCCESS")
        
        # Test Celery broker connection
        print("🔍 Testing Celery broker connection...")
        from kombu import Connection
        with Connection(REDIS_URL, connect_timeout=5) as conn:
            conn.ensure_connection(max_retries=3)
        print("✅ Celery broker connection test: SUCCESS")
        
    except ImportError as e:
        print(f"❌ Required packages not available for Redis testing: {e}")
        print("⚠️  Install 'redis' and 'kombu' packages for connection testing")
    except Exception as e:
        print(f"❌ Redis/Celery connection test failed: {e}")
        print("⚠️  Celery tasks will use memory backend as fallback")
        # Fallback to memory backend if Redis connection fails
        CELERY_BROKER_URL = 'memory://'
        CELERY_RESULT_BACKEND = 'cache+memory://'
        CELERY_TASK_ALWAYS_EAGER = True
else:
    print("⚠️  Skipping Redis connection tests - REDIS_URL not configured")

# =====================================
# EMAIL CONFIGURATION
# =====================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@tudollar.com')

# =====================================
# CORS CONFIGURATION
# =====================================
CORS_ALLOWED_ORIGINS = [
    "https://tudollar-frontend.onrender.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
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
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

CSRF_TRUSTED_ORIGINS = [
    "https://tudollar-backend.onrender.com",
    "https://tudollar-frontend.onrender.com",
    "https://*.onrender.com",
]

# =====================================
# LOGGING CONFIGURATION
# =====================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler', 
            'formatter': 'verbose'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'production.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO', 
            'propagate': False
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'apps.users': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =====================================
# REST FRAMEWORK CONFIG
# =====================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
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

# =====================================
# JWT SETTINGS
# =====================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# =====================================
# APP FEATURES
# =====================================
TRADING_ENABLED = os.getenv('TRADING_ENABLED', 'True').lower() == 'true'
REQUIRE_EMAIL_VERIFICATION = os.getenv('REQUIRE_EMAIL_VERIFICATION', 'False').lower() == 'true'
ALLOW_DEMO_TRADING = True
ENABLE_BACKGROUND_TASKS = os.getenv('ENABLE_BACKGROUND_TASKS', 'true').lower() == 'true'

EXCHANGE_SETTINGS = {
    'BINANCE': {'TESTNET': False},
    'OKX': {'DEMO': False}
}

API_KEY_DEBUG = False

# =====================================
# PERFORMANCE OPTIMIZATIONS
# =====================================
# Database connection optimization
DATABASES['default']['CONN_MAX_AGE'] = 60  # 1 minute connection persistence

# Template configuration
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# =====================================
# STARTUP DIAGNOSTICS
# =====================================
print("🚀 Production Settings Loaded:")
print(f"   DEBUG: {DEBUG}")
print(f"   DATABASE: {DATABASES['default'].get('ENGINE', 'Not configured')}")
print(f"   ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"   TRADING_ENABLED: {TRADING_ENABLED}")
print(f"   REDIS_URL: {'Configured' if REDIS_URL else 'Not configured'}")
print(f"   DATABASE_URL: {'Configured' if os.getenv('DATABASE_URL') else 'Not set - using SQLite fallback'}")
print(f"   ENABLE_BACKGROUND_TASKS: {ENABLE_BACKGROUND_TASKS}")

print("🔧 CORS Configuration:")
print(f"   Allow All Origins: {CORS_ALLOW_ALL_ORIGINS}")
if not CORS_ALLOW_ALL_ORIGINS:
    print(f"   Allowed Origins: {len(CORS_ALLOWED_ORIGINS)} origins configured")
print(f"   Allow Credentials: {CORS_ALLOW_CREDENTIALS}")

print("🔧 Redis Status:")
if REDIS_URL:
    print(f"   ✅ Redis: Configured")
    print(f"   ✅ Celery: Enabled with Redis backend")
    print(f"   ✅ Cache: Redis cache enabled")
    print(f"   ✅ Channels: Redis channel layer enabled")
    print(f"   ✅ Celery Connection Retry: Enabled (max {CELERY_BROKER_CONNECTION_MAX_RETRIES} retries)")
else:
    print(f"   ❌ Redis: Not configured")
    print(f"   ⚠️  Celery: Using memory backend (tasks run synchronously)")
    print(f"   ⚠️  Cache: Using dummy cache")
    print(f"   ⚠️  Channels: Using in-memory layer")

print("🔧 Feature Flags:")
print(f"   Trading: {'✅ Enabled' if TRADING_ENABLED else '❌ Disabled'}")
print(f"   Email Verification: {'✅ Required' if REQUIRE_EMAIL_VERIFICATION else '❌ Not required'}")
print(f"   Background Tasks: {'✅ Enabled' if ENABLE_BACKGROUND_TASKS else '❌ Disabled'}")

# Create logs directory if it doesn't exist
logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
    print(f"📁 Created logs directory: {logs_dir}")

# Final startup message
print("🎯 Production configuration completed successfully!")