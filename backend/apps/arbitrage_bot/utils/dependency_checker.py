# backend/arbitrage_bot/utils/dependency_checker.py
import importlib
import logging

logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are available"""
    dependencies = {
        'ccxt': 'ccxt',
        'websocket': 'websocket-client', 
        'numpy': 'numpy',
        'pandas': 'pandas',
        'celery': 'celery',
        'redis': 'redis',
    }
    
    missing = []
    available = []
    
    for import_name, package_name in dependencies.items():
        try:
            importlib.import_module(import_name)
            available.append(package_name)
            logger.info(f"✓ {package_name} is available")
        except ImportError:
            missing.append(package_name)
            logger.warning(f"✗ {package_name} is missing")
    
    return available, missing

# Run the check when module loads
available_deps, missing_deps = check_dependencies()
if missing_deps:
    logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
    logger.error(f"Please install with: pip install {' '.join(missing_deps)}")