# backend/apps/arbitrage_bot/views/__init__.py
# Import all view functions to make them accessible
from .api_views import *
from .web_views import *
from .admin_views import *
from .trading_views import *
from .performance_views import *

# Export all public names from submodules
__all__ = [name for name in globals().keys() if not name.startswith("_")]

# Re-export the main initialization function
from .api_views import initialize_system