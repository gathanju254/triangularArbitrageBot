# backend/core/cache_utils.py
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def safe_cache_delete_pattern(pattern: str) -> None:
    """
    Safely delete cache keys matching a pattern.
    Works with both Redis and LocMemCache backends.
    """
    try:
        # Try Redis pattern deletion first
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(pattern)
        else:
            # For LocMemCache, we need to handle it differently
            # Since LocMemCache doesn't support pattern deletion,
            # we'll clear the entire cache in development
            # This is acceptable for development purposes
            if hasattr(cache, 'clear'):
                cache.clear()
                logger.info("Cleared entire cache (LocMemCache pattern deletion workaround)")
            else:
                logger.warning("Cache backend doesn't support pattern deletion or clear")
    except Exception as e:
        logger.warning(f"Failed to delete cache pattern {pattern}: {e}")

def safe_cache_delete_keys(keys: list) -> None:
    """
    Safely delete specific cache keys.
    """
    for key in keys:
        try:
            cache.delete(key)
        except Exception as e:
            logger.warning(f"Failed to delete cache key {key}: {e}")

def get_cache_backend_info() -> dict:
    """
    Get information about the current cache backend.
    """
    backend = getattr(cache, 'backend', None)
    return {
        'backend_class': str(type(backend)) if backend else 'Unknown',
        'supports_patterns': hasattr(cache, 'delete_pattern'),
        'supports_clear': hasattr(cache, 'clear') if backend else False,
    }