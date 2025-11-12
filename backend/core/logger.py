# backend/core/logger.py
import logging
import json
from datetime import datetime


def setup_integrated_logging():
    """
    Setup logging configuration for integrated operations.
    This should be called in your Django settings.
    """
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'detailed',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/integrated.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'detailed',
            },
            'json_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/integrated.json',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
            }
        },
        'loggers': {
            'tudollar.integrated': {
                'handlers': ['console', 'file', 'json_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'tudollar.trading': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'tudollar.risk_management': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'tudollar.arbitrage': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    })


def get_integrated_logger():
    """
    Get logger for cross-app operations using standard logging.
    
    Returns:
        logging.Logger: Configured logger for integrated operations
    """
    return logging.getLogger('tudollar.integrated')


def get_app_logger(app_name):
    """
    Get logger for specific application.
    
    Args:
        app_name: Name of the application (e.g., 'trading', 'risk_management')
        
    Returns:
        logging.Logger: Configured logger for the application
    """
    return logging.getLogger(f'tudollar.{app_name}')


def get_service_logger(service_name):
    """
    Get logger for specific service.
    
    Args:
        service_name: Name of the service
        
    Returns:
        logging.Logger: Configured logger for the service
    """
    return logging.getLogger(f'tudollar.services.{service_name}')


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON for structured logging.
    """
    
    def format(self, record):
        """
        Format the log record as JSON.
        """
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'funcName': record.funcName,
            'lineno': record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
            
        return json.dumps(log_entry)


def create_structured_logger(name, level=logging.INFO):
    """
    Create a logger that outputs structured JSON.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        logging.Logger: Configured structured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger