# backend/triangularArbitrageBot/settings/development.py
"""
Development settings for triangularArbitrageBot project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '.localhost',
    '.ngrok.io',  # For ngrok tunneling
]

# Database
# Using SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email configuration for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar (optional)
try:
    import debug_toolbar
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# More verbose logging in development
LOGGING['loggers']['apps.arbitrage_bot']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Less restrictive throttling for development
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '1000/hour',
    'user': '10000/hour'
}

# Development-specific trading configuration
TRADING_CONFIG.update({
    'min_profit_threshold': 0.1,  # Lower threshold for testing
    'max_position_size': 100,  # Smaller position size for testing
    'use_testnet': True,  # Always use testnet in development
})

print("Development settings loaded - Using testnet and relaxed limits")