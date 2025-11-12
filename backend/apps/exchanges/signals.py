# backend/apps/exchanges/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import Exchange, MarketData, ExchangeCredentials


@receiver(pre_save, sender=ExchangeCredentials)
def validate_credentials(sender, instance, **kwargs):
    """
    Validate exchange credentials before saving (sync check for obvious errors)
    """
    if not instance.is_validated:
        try:
            instance.validate_credentials()
        except Exception as e:
            print(f"[!] Pre-save validation failed: {str(e)}")


@receiver(post_save, sender=ExchangeCredentials)
def async_validate_credentials(sender, instance, created, **kwargs):
    """
    Validate exchange credentials asynchronously after save,
    ensuring it happens after DB commit to avoid premature queries.
    """
    if created or not instance.is_validated:
        transaction.on_commit(lambda: validate_credentials_async(instance.id))


def validate_credentials_async(credentials_id):
    """
    Async background validation of exchange credentials
    """
    try:
        from .models import ExchangeCredentials
        from .services import CredentialsService

        credentials = ExchangeCredentials.objects.get(id=credentials_id)
        credentials_service = CredentialsService(credentials)
        credentials_service.validate_credentials()
        print(f"[✓] Async credentials validation complete for {credentials.exchange_name}")

    except Exception as e:
        print(f"[✗] Async validation failed for credentials ID {credentials_id}: {str(e)}")


@receiver(post_save, sender=MarketData)
def check_arbitrage_opportunities(sender, instance, created, **kwargs):
    """
    Check for arbitrage opportunities when new market data arrives
    """
    if created:
        try:
            from apps.arbitrage.tasks import scan_arbitrage_opportunities
            scan_arbitrage_opportunities.delay(instance.symbol)
            print(f"[→] Arbitrage scan triggered for {instance.symbol}")
        except Exception as e:
            print(f"[!] Failed to trigger arbitrage scan: {str(e)}")
