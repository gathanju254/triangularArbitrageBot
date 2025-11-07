# backend/fix_time_sync.py
import requests
import time
import os
from datetime import datetime

def sync_system_time():
    """Sync system time with Binance server time"""
    print("🕒 Synchronizing system time with Binance...")
    
    try:
        # Get Binance server time
        response = requests.get('https://api.binance.com/api/v3/time')
        binance_time = response.json()['serverTime'] / 1000  # Convert to seconds
        binance_time_str = datetime.fromtimestamp(binance_time).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get local time
        local_time = time.time()
        local_time_str = datetime.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')
        
        time_diff = binance_time - local_time
        print(f"📊 Binance Server Time: {binance_time_str}")
        print(f"📊 Your Local Time: {local_time_str}")
        print(f"⏱️ Time Difference: {time_diff:.2f} seconds")
        
        if abs(time_diff) > 30:  # More than 30 seconds difference
            print(f"❌ CRITICAL: Your system time is {abs(time_diff):.2f} seconds out of sync!")
            print("💡 Please sync your system clock:")
            print("   Windows: w32tm /resync")
            print("   Linux/Mac: sudo ntpdate -s time.nist.gov")
            return False
        elif abs(time_diff) > 5:  # More than 5 seconds difference
            print(f"⚠️ WARNING: Your system time is {abs(time_diff):.2f} seconds out of sync")
            return True
        else:
            print("✅ System time is properly synchronized")
            return True
            
    except Exception as e:
        print(f"❌ Error syncing time: {e}")
        return False

if __name__ == "__main__":
    sync_system_time()