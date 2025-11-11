# backend/apps/exchanges/management/commands/create_exchanges.py

from django.core.management.base import BaseCommand
from apps.exchanges.models import Exchange

class Command(BaseCommand):
    help = 'Create initial exchange records'

    def handle(self, *args, **options):
        exchanges_data = [
            {
                'name': 'Binance',
                'code': 'binance',
                'exchange_type': 'cex',
                'base_url': 'https://api.binance.com',
                'api_documentation': 'https://binance-docs.github.io/apidocs/',
                'trading_fee': 0.001,
            },
            {
                'name': 'KuCoin',
                'code': 'kucoin', 
                'exchange_type': 'cex',
                'base_url': 'https://api.kucoin.com',
                'api_documentation': 'https://docs.kucoin.com/',
                'trading_fee': 0.001,
            },
            {
                'name': 'Coinbase',
                'code': 'coinbase',
                'exchange_type': 'cex', 
                'base_url': 'https://api.coinbase.com',
                'api_documentation': 'https://docs.cloud.coinbase.com/',
                'trading_fee': 0.005,
            },
            {
                'name': 'Kraken',
                'code': 'kraken',
                'exchange_type': 'cex',
                'base_url': 'https://api.kraken.com',
                'api_documentation': 'https://docs.kraken.com/',
                'trading_fee': 0.0026,
            },
            {
                'name': 'Huobi',
                'code': 'huobi',
                'exchange_type': 'cex',
                'base_url': 'https://api.huobi.pro',
                'api_documentation': 'https://huobiapi.github.io/docs/',
                'trading_fee': 0.002,
            },
            {
                'name': 'OKX',
                'code': 'okx',
                'exchange_type': 'cex',
                'base_url': 'https://www.okx.com',
                'api_documentation': 'https://www.okx.com/docs/',
                'trading_fee': 0.0008,  # 0.08% maker fee
            }
        ]

        for exchange_data in exchanges_data:
            exchange, created = Exchange.objects.get_or_create(
                code=exchange_data['code'],
                defaults=exchange_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created exchange: {exchange.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Exchange already exists: {exchange.name}')
                )