# backend/tudollar_backend/settings/base.py
# backend/tudollar_backend/settings/base.py
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from cryptography.fernet import Fernet  # Add this import

# Load environment variables from .env if present
load_dotenv()

# --- Base Directories ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Security & Core Settings ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# --- Encryption Settings ---
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    # In production, this should always be set in environment
    if os.getenv('DJANGO_ENV') == 'production':
        raise ValueError("ENCRYPTION_KEY must be set in production environment")
    else:
        # For development, generate a key if not set
        ENCRYPTION_KEY = Fernet.generate_key().decode()
        print(f"⚠️  WARNING: ENCRYPTION_KEY not set. Generated temporary key for development.")
        print(f"⚠️  Set ENCRYPTION_KEY in your environment for production use.")

# --- Authentication & User Model ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Custom user model
AUTH_USER_MODEL = 'users.User'

# --- Installed Apps ---
INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party Apps
    'rest_framework',
    'corsheaders',
    'channels',
    'django_celery_beat',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',

    # Local Apps
    'apps.users',
    'apps.arbitrage',
    'apps.exchanges',
    'apps.trading',
    'apps.analytics',
    'apps.notifications',
    'apps.risk_management',
    'apps.dashboard',
    'apps.settings',
]

# --- Middleware ---
MIDDLEWARE = [
    # Django core middleware first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom middleware after authentication
    'core.middleware.RequestLoggingMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RateLimitMiddleware',
]

# --- URL & WSGI / ASGI Configuration ---
ROOT_URLCONF = 'tudollar_backend.urls'
WSGI_APPLICATION = 'tudollar_backend.wsgi.application'
ASGI_APPLICATION = 'tudollar_backend.asgi.application'

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# --- Database (Default: SQLite, override in local/production) ---
DATABASES = {
    'default': {
        'ENGINE': os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        'NAME': os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        'USER': os.getenv("DB_USER", ""),
        'PASSWORD': os.getenv("DB_PASSWORD", ""),
        'HOST': os.getenv("DB_HOST", ""),
        'PORT': os.getenv("DB_PORT", ""),
    }
}

# --- Static & Media Files ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Django REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.authentication.CustomJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/day',
        'burst': '60/minute',
        'sustained': '1000/hour'
    }
}

# --- JWT Authentication ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv("JWT_ACCESS_LIFETIME", 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv("JWT_REFRESH_LIFETIME", 1))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    
    # Custom settings
    'ISSUER': 'tudollar-backend',
    'ALGORITHM': 'HS256',
}

# --- CORS ---
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "True").lower() == "true"
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if not CORS_ALLOW_ALL_ORIGINS else []

# Allow credentials for JWT
CORS_ALLOW_CREDENTIALS = True

# CORS allowed methods and headers
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

# --- Celery Configuration ---
# Celery Configuration Options
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True

# Broker settings (Redis)
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Serialization
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Beat Scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Task execution settings
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
CELERY_TASK_IGNORE_RESULT = False
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# Queue routing
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_CREATE_MISSING_QUEUES = True

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

# Beat Schedule (moved to celery.py for better organization)
# CELERY_BEAT_SCHEDULE is defined in celery.py

# --- Channels (WebSocket) ---
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(
                os.getenv('REDIS_HOST', 'redis'),
                int(os.getenv('REDIS_PORT', 6379))
            )],
        },
    },
}

# --- Security Settings ---
# SSL/HTTPS settings (for production)
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'

# --- Email Settings ---
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@tudollar.com')

# Email verification requirement
REQUIRE_EMAIL_VERIFICATION = os.getenv('REQUIRE_EMAIL_VERIFICATION', 'False').lower() == 'true'

# --- Service Configuration ---
# Service API key for internal communication
SERVICE_API_KEY = os.getenv('SERVICE_API_KEY', 'your-service-api-key-change-in-production')

# Remove the old ENCRYPTION_KEY line since it's now handled above
# ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-encryption-key-change-in-production')

# --- Logging Configuration ---
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
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
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
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Default primary key field type ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Tudollar Specific Settings ---
# Trading settings
TRADING_ENABLED = os.getenv('TRADING_ENABLED', 'True').lower() == 'true'
MAX_TRADE_SIZE = float(os.getenv('MAX_TRADE_SIZE', '10000.0'))
MIN_PROFIT_THRESHOLD = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5'))

# Risk management settings
RISK_ENABLED = os.getenv('RISK_ENABLED', 'True').lower() == 'true'
MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '1000.0'))
MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '5000.0'))

# Exchange settings
SUPPORTED_EXCHANGES = os.getenv('SUPPORTED_EXCHANGES', 'binance,coinbase,kraken').split(',')
DEFAULT_EXCHANGES = os.getenv('DEFAULT_EXCHANGES', 'binance,coinbase').split(',')

# WebSocket settings
WEBSOCKET_ENABLED = os.getenv('WEBSOCKET_ENABLED', 'True').lower() == 'true'
WEBSOCKET_HEARTBEAT = int(os.getenv('WEBSOCKET_HEARTBEAT', '30'))