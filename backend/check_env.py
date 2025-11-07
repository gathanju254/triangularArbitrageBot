# backend/check_env.py
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Checking Environment Variables...")
print(f"BINANCE_API_KEY: {'✅ Loaded' if os.getenv('BINANCE_API_KEY') else '❌ Missing'}")
print(f"BINANCE_SECRET_KEY: {'✅ Loaded' if os.getenv('BINANCE_SECRET_KEY') else '❌ Missing'}")
print(f"KRAKEN_API_KEY: {'✅ Loaded' if os.getenv('KRAKEN_API_KEY') else '❌ Missing'}")
print(f"KRAKEN_SECRET_KEY: {'✅ Loaded' if os.getenv('KRAKEN_SECRET_KEY') else '❌ Missing'}")

# Test Binance connection
try:
    import ccxt
    exchange = ccxt.binance({
        'apiKey': os.getenv('BINANCE_API_KEY'),
        'secret': os.getenv('BINANCE_SECRET_KEY'),
        'sandbox': False,
    })
    
    # Test with public method first
    ticker = exchange.fetch_ticker('BTC/USDT')
    print("✅ Binance public API connection: SUCCESS")
    
    # Test with private method (if keys are provided)
    if os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_SECRET_KEY'):
        try:
            balance = exchange.fetch_balance()
            print("✅ Binance private API connection: SUCCESS")
        except Exception as e:
            print(f"⚠️ Binance private API connection: {e}")
            
except Exception as e:
    print(f"❌ Binance connection failed: {e}")