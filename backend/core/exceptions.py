# backend/core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.http import JsonResponse
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class TudollarBaseException(APIException):
    """
    Base exception for all Tudollar custom exceptions.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'
    default_code = 'error'
    
    def __init__(self, detail=None, code=None, extra_data=None):
        if detail is not None:
            self.detail = detail
        if code is not None:
            self.code = code
        self.extra_data = extra_data or {}


class ExchangeConnectionError(TudollarBaseException):
    """
    Raised when there's an issue connecting to an exchange.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Unable to connect to exchange.'
    default_code = 'exchange_connection_error'


class InsufficientFundsError(TudollarBaseException):
    """
    Raised when there are insufficient funds for a trade.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Insufficient funds for this operation.'
    default_code = 'insufficient_funds'


class RiskLimitExceededError(TudollarBaseException):
    """
    Raised when a trade would exceed risk limits.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Operation would exceed risk limits.'
    default_code = 'risk_limit_exceeded'


class InvalidOrderError(TudollarBaseException):
    """
    Raised when an order is invalid.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid order parameters.'
    default_code = 'invalid_order'


class MarketDataError(TudollarBaseException):
    """
    Raised when there's an issue with market data.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Market data error occurred.'
    default_code = 'market_data_error'


class TradingDisabledError(TudollarBaseException):
    """
    Raised when trading is disabled for a user or system.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Trading is currently disabled.'
    default_code = 'trading_disabled'


class CircuitBreakerTriggeredError(TudollarBaseException):
    """
    Raised when a circuit breaker has been triggered.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Circuit breaker triggered. Please try again later.'
    default_code = 'circuit_breaker_triggered'


# =============================================================================
# INTEGRATED TRADING EXCEPTIONS
# =============================================================================

class IntegratedTradingError(TudollarBaseException):
    """Raised when integrated trading operations fail"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Integrated trading operation failed.'
    default_code = 'integrated_trading_error'


class RiskComplianceError(TudollarBaseException):
    """
    Raised when a trade fails risk compliance checks.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Trade failed risk compliance checks.'
    default_code = 'risk_compliance_error'


class ArbitrageExecutionError(TudollarBaseException):
    """
    Raised when arbitrage trade execution fails.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Arbitrage trade execution failed.'
    default_code = 'arbitrage_execution_error'


class CrossAppIntegrationError(TudollarBaseException):
    """
    Raised when integration between different apps fails.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Cross-application integration error occurred.'
    default_code = 'cross_app_integration_error'


class ServiceUnavailableError(TudollarBaseException):
    """
    Raised when a required service is unavailable.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Required service is temporarily unavailable.'
    default_code = 'service_unavailable'


class DataConsistencyError(TudollarBaseException):
    """
    Raised when data consistency issues are detected across services.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Data consistency error detected.'
    default_code = 'data_consistency_error'


class LimitMonitoringError(TudollarBaseException):
    """
    Raised when limit monitoring operations fail.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Limit monitoring operation failed.'
    default_code = 'limit_monitoring_error'


class OrderIntegrationError(TudollarBaseException):
    """
    Raised when order integration between trading and arbitrage fails.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Order integration failed.'
    default_code = 'order_integration_error'


class RiskMetricsError(TudollarBaseException):
    """
    Raised when risk metrics calculation or update fails.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Risk metrics operation failed.'
    default_code = 'risk_metrics_error'


class ConfigurationError(TudollarBaseException):
    """
    Raised when configuration issues are detected.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Configuration error detected.'
    default_code = 'configuration_error'


class ValidationIntegrationError(TudollarBaseException):
    """
    Raised when cross-service validation fails.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Cross-service validation failed.'
    default_code = 'validation_integration_error'


class TimeoutIntegrationError(TudollarBaseException):
    """
    Raised when integrated operations timeout.
    """
    status_code = status.HTTP_408_REQUEST_TIMEOUT
    default_detail = 'Integrated operation timed out.'
    default_code = 'timeout_integration_error'


class ResourceLockedError(TudollarBaseException):
    """
    Raised when a resource is locked by another process.
    """
    status_code = status.HTTP_423_LOCKED
    default_detail = 'Resource is currently locked.'
    default_code = 'resource_locked_error'


class ConcurrentModificationError(TudollarBaseException):
    """
    Raised when concurrent modification is detected.
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Concurrent modification detected.'
    default_code = 'concurrent_modification_error'


class DependencyError(TudollarBaseException):
    """
    Raised when a dependency service fails.
    """
    status_code = status.HTTP_424_FAILED_DEPENDENCY
    default_detail = 'Dependency service failed.'
    default_code = 'dependency_error'


# =============================================================================
# EXCEPTION HANDLER
# =============================================================================

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that provides consistent error responses.
    Enhanced to handle integrated trading exceptions.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get request information for logging
    request = context.get('request', {})
    user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
    view_name = context.get('view', None).__class__.__name__ if context.get('view') else 'UnknownView'
    
    if response is not None:
        # Customize the error response for Tudollar exceptions
        if isinstance(exc, TudollarBaseException):
            error_response = {
                'error': {
                    'code': exc.code,
                    'message': exc.detail,
                    'type': exc.__class__.__name__,
                    'status_code': response.status_code,
                }
            }
            
            # Add extra data if available
            if exc.extra_data:
                error_response['error']['details'] = exc.extra_data
            
            response.data = error_response
            
            # Log integrated exceptions with context
            if isinstance(exc, (IntegratedTradingError, CrossAppIntegrationError)):
                logger.warning(
                    "Integrated exception occurred - Type: %s, User: %s, View: %s, Code: %s, Status: %s, Details: %s",
                    exc.__class__.__name__,
                    user_id,
                    view_name,
                    exc.code,
                    response.status_code,
                    exc.extra_data
                )
            else:
                logger.info(
                    "Business exception handled - Type: %s, User: %s, View: %s, Code: %s, Status: %s",
                    exc.__class__.__name__,
                    user_id,
                    view_name,
                    exc.code,
                    response.status_code
                )
                
        else:
            # Handle standard DRF exceptions
            response.data = {
                'error': {
                    'code': getattr(exc, 'code', 'unknown_error'),
                    'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
                    'type': exc.__class__.__name__,
                    'status_code': response.status_code,
                }
            }
            
            logger.warning(
                "DRF exception handled - Type: %s, User: %s, View: %s, Status: %s",
                exc.__class__.__name__,
                user_id,
                view_name,
                response.status_code
            )
    else:
        # Handle non-DRF exceptions
        logger.error(
            "Unhandled exception occurred - Type: %s, User: %s, View: %s, Message: %s, Path: %s",
            exc.__class__.__name__,
            user_id,
            view_name,
            str(exc),
            getattr(request, 'path', 'Unknown'),
            exc_info=True
        )
        
        response = JsonResponse({
            'error': {
                'code': 'internal_server_error',
                'message': 'An internal server error occurred.',
                'type': 'InternalServerError',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Add CORS headers if needed
    if hasattr(response, 'headers'):
        response.headers['X-Error-Type'] = exc.__class__.__name__ if hasattr(exc, '__class__') else 'Unknown'
    
    return response


def handle_uncaught_exception(request, exception):
    """
    Handle uncaught exceptions in Django views.
    Enhanced with integrated error context.
    """
    user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
    
    logger.error(
        "Uncaught exception in view - Type: %s, User: %s, Path: %s, Method: %s, Message: %s",
        exception.__class__.__name__,
        user_id,
        request.path,
        request.method,
        str(exception),
        exc_info=True
    )
    
    return JsonResponse({
        'error': {
            'code': 'internal_server_error',
            'message': 'An unexpected error occurred.',
            'type': 'InternalServerError',
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# EXCEPTION UTILITIES
# =============================================================================

def handle_integrated_operation(operation_name, operation_func, *args, **kwargs):
    """
    Utility function to handle integrated operations with proper exception handling.
    
    Args:
        operation_name: Name of the operation for logging
        operation_func: Function to execute
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Operation result
        
    Raises:
        IntegratedTradingError: If the operation fails
    """
    try:
        return operation_func(*args, **kwargs)
    except TudollarBaseException:
        # Re-raise known Tudollar exceptions
        raise
    except Exception as e:
        logger.error(
            "Integrated operation failed - Operation: %s, Error: %s, Type: %s",
            operation_name,
            str(e),
            e.__class__.__name__,
            exc_info=True
        )
        raise IntegratedTradingError(
            detail=f"{operation_name} failed: {str(e)}",
            extra_data={'operation': operation_name, 'original_error': str(e)}
        )


def ensure_risk_compliance(user, trade_data):
    """
    Utility to ensure risk compliance with proper exception handling.
    
    Args:
        user: User object
        trade_data: Trade data dictionary
        
    Raises:
        RiskComplianceError: If risk compliance check fails
    """
    try:
        from apps.risk_management.services import RiskManagementService
        
        is_compliant, message = RiskManagementService.check_trade_compliance(user, trade_data)
        
        if not is_compliant:
            raise RiskComplianceError(
                detail=message,
                extra_data={'trade_data': trade_data, 'user_id': user.id}
            )
            
    except RiskComplianceError:
        raise
    except Exception as e:
        logger.error(
            "Risk compliance check failed - User: %s, Trade Data: %s, Error: %s",
            user.id,
            trade_data,
            e.__class__.__name__,
            exc_info=True
        )
        raise RiskComplianceError(
            detail=f"Risk compliance check failed: {str(e)}",
            extra_data={'trade_data': trade_data, 'user_id': user.id}
        )


def validate_arbitrage_opportunity(user, opportunity_id, amount):
    """
    Utility to validate arbitrage opportunity with proper exception handling.
    
    Args:
        user: User object
        opportunity_id: Arbitrage opportunity ID
        amount: Trade amount
        
    Raises:
        ArbitrageExecutionError: If validation fails
    """
    try:
        from apps.arbitrage.services import ArbitrageService
        from apps.arbitrage.models import ArbitrageOpportunity
        
        opportunity = ArbitrageOpportunity.objects.get(id=opportunity_id, status='active')
        is_valid, message = ArbitrageService.validate_opportunity(opportunity, user)
        
        if not is_valid:
            raise ArbitrageExecutionError(
                detail=message,
                extra_data={
                    'opportunity_id': opportunity_id,
                    'amount': float(amount),
                    'user_id': user.id
                }
            )
            
    except ArbitrageOpportunity.DoesNotExist:
        raise ArbitrageExecutionError(
            detail="Arbitrage opportunity not found or no longer active",
            extra_data={'opportunity_id': opportunity_id, 'user_id': user.id}
        )
    except ArbitrageExecutionError:
        raise
    except Exception as e:
        logger.error(
            "Arbitrage opportunity validation failed - User: %s, Opportunity: %s, Amount: %s, Error: %s",
            user.id,
            opportunity_id,
            float(amount),
            e.__class__.__name__,
            exc_info=True
        )
        raise ArbitrageExecutionError(
            detail=f"Opportunity validation failed: {str(e)}",
            extra_data={'opportunity_id': opportunity_id, 'user_id': user.id}
        )


# =============================================================================
# LOGGING UTILITIES (Using standard logging)
# =============================================================================

def get_integrated_logger():
    """
    Get logger for cross-app operations using standard logging.
    
    Returns:
        logging.Logger: Configured logger for integrated operations
    """
    return logging.getLogger('tudollar.integrated')


def log_integrated_operation(operation, **context):
    """
    Convenience function for logging integrated operations.
    
    Args:
        operation: Name of the operation
        **context: Additional context for logging
    """
    logger = get_integrated_logger()
    logger.info("Integrated operation: %s - Context: %s", operation, context)


def log_cross_app_flow(flow_name, from_app, to_app, user_id=None, **extra):
    """
    Log cross-application flow events.
    
    Args:
        flow_name: Name of the flow
        from_app: Source application
        to_app: Target application
        user_id: User ID if available
        **extra: Additional context
    """
    logger = get_integrated_logger()
    context = {
        'flow': flow_name,
        'from_app': from_app,
        'to_app': to_app,
        'user_id': user_id,
        **extra
    }
    logger.info("Cross-app flow: %s -> %s: %s - Context: %s", from_app, to_app, flow_name, context)


def log_service_dependency(service_name, operation, status, duration_ms=None, **extra):
    """
    Log service dependency calls.
    
    Args:
        service_name: Name of the dependent service
        operation: Operation being performed
        status: Status of the operation ('success', 'failure', 'timeout')
        duration_ms: Operation duration in milliseconds
        **extra: Additional context
    """
    logger = get_integrated_logger()
    duration_info = f" in {duration_ms}ms" if duration_ms else ""
    logger.info("Service dependency: %s.%s - Status: %s%s - Context: %s", 
                service_name, operation, status, duration_info, extra)


class IntegratedLogger:
    """
    Simple logger wrapper for integrated operations using standard logging.
    """
    
    def __init__(self, name='tudollar.integrated'):
        self.logger = logging.getLogger(name)
    
    def log_operation(self, operation, level='info', **context):
        """
        Log an integrated operation.
        
        Args:
            operation: Operation name
            level: Log level ('info', 'warning', 'error')
            **context: Operation context
        """
        log_method = getattr(self.logger, level, self.logger.info)
        log_method("Operation: %s - Context: %s", operation, context)
    
    def log_flow(self, flow_type, source, target, user_id=None, **extra):
        """
        Log cross-app flow.
        
        Args:
            flow_type: Type of flow
            source: Source application/service
            target: Target application/service
            user_id: User ID if available
            **extra: Additional context
        """
        context = {
            'flow_type': flow_type,
            'source': source,
            'target': target,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            **extra
        }
        self.logger.info("Flow: %s -> %s: %s - Context: %s", source, target, flow_type, context)
    
    def log_dependency(self, service, operation, status, duration=None, error=None, **extra):
        """
        Log service dependency call.
        
        Args:
            service: Service name
            operation: Operation performed
            status: Status ('success', 'failure', 'timeout')
            duration: Operation duration in seconds
            error: Error message if any
            **extra: Additional context
        """
        context = {
            'service': service,
            'operation': operation,
            'status': status,
            'duration': duration,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            **extra
        }
        
        if status == 'success':
            self.logger.info("Dependency success: %s.%s - Duration: %s", service, operation, duration)
        else:
            self.logger.warning("Dependency issue: %s.%s - Status: %s - Error: %s", 
                              service, operation, status, error)