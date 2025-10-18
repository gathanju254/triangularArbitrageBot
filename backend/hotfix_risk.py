# backend/hotfix_risk.py
import os
import django
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from arbitrage_bot.models.trade import BotConfig

def apply_hotfix():
    """Apply immediate fixes to risk management settings"""
    try:
        config, created = BotConfig.objects.get_or_create(pk=1)
        
        # Set reasonable defaults
        config.min_profit_threshold = 0.1  # Lower threshold to allow more trades
        config.max_position_size = 100.0
        config.max_daily_loss = 50.0
        config.max_drawdown = 20.0
        config.base_balance = 1000.0
        
        config.save()
        print("✅ Hotfix applied: Risk settings updated")
        print(f"   - Min Profit Threshold: {config.min_profit_threshold}%")
        print(f"   - Max Position Size: ${config.max_position_size}")
        print(f"   - Max Daily Loss: ${config.max_daily_loss}")
        
    except Exception as e:
        print(f"❌ Hotfix failed: {e}")

if __name__ == "__main__":
    apply_hotfix()