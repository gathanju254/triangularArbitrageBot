from celery import shared_task
from .services import MarketDataService, ExchangeFactory

@shared_task
def sync_all_exchanges_market_data():
    """Sync market data for all active exchanges"""
    MarketDataService.update_market_data()

@shared_task
def update_exchange_balances():
    """Update balances for all active exchanges"""
    for exchange_service in ExchangeFactory.get_all_active_exchanges():
        try:
            exchange_service.get_balance()
        except Exception:
            continue

@shared_task
def test_exchange_connectivity():
    """Test connectivity for all active exchanges"""
    for exchange_service in ExchangeFactory.get_all_active_exchanges():
        try:
            status = exchange_service.get_exchange_status()
            # Optionally log or store status
        except Exception:
            continue