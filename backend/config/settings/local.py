# backend/tudollar_backend/settings/local.py
from .development import *

# Local overrides
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Local development settings
CORS_ALLOW_ALL_ORIGINS = True