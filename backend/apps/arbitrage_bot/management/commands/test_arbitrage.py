from django.core.management.base import BaseCommand
from arbitrage_bot.core.arbitrage_engine import ArbitrageEngine
from arbitrage_bot.core.market_data import MarketDataManager

class Command(BaseCommand):
    help = 'Test arbitrage engine functionality'
    
    def handle(self, *args, **options):
        manager = MarketDataManager()
        engine = ArbitrageEngine()
        
        # Test with sample data
        sample_prices = {
            'BTC/USDT': 45000.0,
            'ETH/USDT': 2700.0,
            'BNB/USDT': 320.0,
            'ETH/BTC': 0.06,
            'USDT/BTC': 0.000022
        }
        
        triangles = engine.find_triangles(list(sample_prices.keys()))
        self.stdout.write(f"Found {len(triangles)} triangles")
        
        opportunities = engine.scan_opportunities(sample_prices)
        self.stdout.write(f"Found {len(opportunities)} opportunities")
        
        for opp in opportunities:
            self.stdout.write(f"Triangle: {opp.triangle}, Profit: {opp.profit_percentage:.4f}%")