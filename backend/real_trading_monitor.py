# backend/real_trading_monitor.py
import requests
import time
import json
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealTradingMonitor:
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.profit_threshold = 0.3  # Will be updated from settings
        self.trade_amount = 10       # $10 per trade to start
        self.check_interval = 5      # Check every 5 seconds
        self.settings_update_interval = 30  # Update settings every 30 seconds
        self.last_settings_update = 0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        self.running = False
        
    def update_profit_threshold(self):
        """Update profit threshold from current settings"""
        try:
            response = requests.get(f"{self.base_url}/settings/", timeout=10)
            if response.status_code == 200:
                settings_data = response.json()
                new_threshold = settings_data.get('settings', {}).get('minProfitThreshold', 0.3)
                if new_threshold != self.profit_threshold:
                    self.profit_threshold = new_threshold
                    logger.info(f"Updated profit threshold to {self.profit_threshold}%")
                return True
            else:
                logger.warning(f"Failed to fetch settings: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Could not update profit threshold: {e}")
            return False
    
    def update_trade_amount(self):
        """Update trade amount from risk limits"""
        try:
            response = requests.get(f"{self.base_url}/risk/metrics/", timeout=10)
            if response.status_code == 200:
                risk_data = response.json()
                max_position = risk_data.get('risk_metrics', {}).get('risk_limits', {}).get('max_position_size', 100)
                # Use 20% of max position size or keep current amount
                new_amount = min(max_position * 0.2, self.trade_amount)
                if new_amount != self.trade_amount and new_amount >= 10:  # Minimum $10
                    self.trade_amount = new_amount
                    logger.info(f"Updated trade amount to ${self.trade_amount}")
        except Exception as e:
            logger.debug(f"Could not update trade amount: {e}")
    
    def enable_real_trading(self):
        """Enable real trading mode"""
        try:
            response = requests.post(f"{self.base_url}/trading/enable_real/", timeout=10)
            if response.status_code == 200:
                logger.info("✅ REAL TRADING ENABLED")
                return True
            else:
                logger.error("❌ Failed to enable real trading")
                return False
        except Exception as e:
            logger.error(f"❌ Error enabling real trading: {e}")
            return False
    
    def should_update_settings(self):
        """Check if it's time to update settings"""
        current_time = time.time()
        if current_time - self.last_settings_update >= self.settings_update_interval:
            self.last_settings_update = current_time
            return True
        return False
    
    def check_system_health(self):
        """Check system health before trading"""
        try:
            health_response = requests.get(f"{self.base_url}/health/", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                if health_data.get('status') == 'healthy':
                    return True
                else:
                    logger.warning(f"System health degraded: {health_data.get('status')}")
                    return False
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def execute_trade(self, opportunity):
        """Execute a single trade with enhanced validation"""
        try:
            # Validate opportunity
            profit_pct = float(opportunity.get('profit_percentage', 0.0))
            triangle = opportunity.get('triangle', [])
            
            if not triangle or len(triangle) != 3:
                logger.error("Invalid triangle format")
                return False
            
            # Check risk metrics before trading
            risk_response = requests.get(f"{self.base_url}/risk/metrics/", timeout=10)
            if risk_response.status_code == 200:
                risk_data = risk_response.json()
                risk_metrics = risk_data.get('risk_metrics', {})
                
                # Check daily loss limit
                daily_pnl = risk_metrics.get('daily_pnl', 0)
                max_daily_loss = risk_metrics.get('risk_limits', {}).get('max_daily_loss', 50)
                if daily_pnl <= -max_daily_loss:
                    logger.warning(f"Daily loss limit reached: ${daily_pnl}")
                    return False
                
                # Check drawdown
                drawdown = risk_metrics.get('drawdown_percentage', 0)
                max_drawdown = risk_metrics.get('risk_limits', {}).get('max_drawdown', 20)
                if drawdown >= max_drawdown:
                    logger.warning(f"Max drawdown reached: {drawdown}%")
                    return False
            
            # Execute trade
            trade_data = {
                "triangle": triangle,
                "amount": self.trade_amount,
                "exchange": "binance"
            }
            
            trade_response = requests.post(
                f"{self.base_url}/trading/execute/", 
                json=trade_data,
                timeout=30
            )
            trade_result = trade_response.json()
            
            if trade_result.get('status') == 'executed':
                profit_amount = float(trade_result.get('profit', 0.0))
                real_trade = trade_result.get('real_trade', False)
                trade_type = "REAL" if real_trade else "SIMULATED"
                
                logger.info(f"✅ {trade_type} TRADE EXECUTED: ${profit_amount:.4f} profit ({profit_pct:.4f}%)")
                self.consecutive_failures = 0
                return True
            else:
                error_msg = trade_result.get('error', 'Unknown error')
                logger.error(f"❌ Trade failed: {error_msg}")
                self.consecutive_failures += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            self.consecutive_failures += 1
            return False
    
    def monitor_and_trade(self):
        """Continuous monitoring and trading with enhanced logic"""
        logger.info("🚀 Starting Real Trading Monitor...")
        self.running = True
        
        # Initial settings update
        self.update_profit_threshold()
        self.update_trade_amount()
        
        # Enable real trading
        real_trading_enabled = self.enable_real_trading()
        if not real_trading_enabled:
            logger.info("Continuing in simulation mode...")
        
        while self.running:
            try:
                # Update settings periodically
                if self.should_update_settings():
                    self.update_profit_threshold()
                    self.update_trade_amount()
                
                # Check system health
                if not self.check_system_health():
                    logger.warning("System health check failed, waiting...")
                    time.sleep(10)
                    continue
                
                # Get current opportunities
                opportunities_response = requests.get(f"{self.base_url}/opportunities/", timeout=10)
                opportunities_data = opportunities_response.json()
                
                # Get risk metrics for display
                risk_response = requests.get(f"{self.base_url}/risk/metrics/", timeout=10)
                risk_data = risk_response.json() if risk_response.status_code == 200 else {}
                
                current_time = datetime.now().strftime('%H:%M:%S')
                risk_metrics = risk_data.get('risk_metrics', {})
                
                if opportunities_data.get('count', 0) > 0:
                    best_opp = opportunities_data['opportunities'][0]
                    profit_pct = float(best_opp.get('profit_percentage', 0.0))
                    
                    logger.info(
                        f"[{current_time}] Best: {profit_pct:.4f}% | "
                        f"Balance: ${risk_metrics.get('current_balance', 0):.2f} | "
                        f"Trades: {risk_metrics.get('total_trades', 0)} | "
                        f"Threshold: {self.profit_threshold}%"
                    )
                    
                    # Auto-execute if profit > threshold
                    if profit_pct > self.profit_threshold:
                        success = self.execute_trade(best_opp)
                        if success:
                            # Small delay after successful trade
                            time.sleep(2)
                    else:
                        logger.debug(f"Profit {profit_pct:.4f}% below threshold {self.profit_threshold}%")
                
                else:
                    logger.info(
                        f"[{current_time}] No opportunities | "
                        f"Balance: ${risk_metrics.get('current_balance', 0):.2f}"
                    )
                
                # Stop if too many consecutive failures
                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.error(f"🛑 Too many consecutive failures ({self.consecutive_failures}). Stopping monitor.")
                    break
                
                time.sleep(self.check_interval)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Network error: {e}")
                self.consecutive_failures += 1
                time.sleep(10)
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                self.consecutive_failures += 1
                time.sleep(10)
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("🛑 Stopping monitoring...")
    
    def get_trading_summary(self):
        """Get comprehensive trading summary"""
        try:
            risk_response = requests.get(f"{self.base_url}/risk/metrics/", timeout=10)
            risk_data = risk_response.json() if risk_response.status_code == 200 else {}
            
            performance_response = requests.get(f"{self.base_url}/performance/", timeout=10)
            performance_data = performance_response.json() if performance_response.status_code == 200 else {}
            
            risk_metrics = risk_data.get('risk_metrics', {})
            execution_stats = risk_data.get('execution_stats', {})
            
            print("\n" + "="*60)
            print("TRADING SUMMARY")
            print("="*60)
            print(f"Current Balance: ${risk_metrics.get('current_balance', 0):.2f}")
            print(f"Peak Balance: ${risk_metrics.get('peak_balance', 0):.2f}")
            print(f"Total Profit: ${risk_metrics.get('total_profit', 0):.2f}")
            print(f"Daily P&L: ${risk_metrics.get('daily_pnl', 0):.2f}")
            print(f"Total Trades: {risk_metrics.get('total_trades', 0)}")
            print(f"Success Rate: {risk_metrics.get('success_rate', 0):.1f}%")
            print(f"Drawdown: {risk_metrics.get('drawdown_percentage', 0):.1f}%")
            print(f"Real Trading: {execution_stats.get('real_trading_enabled', False)}")
            print(f"Profit Threshold: {self.profit_threshold}%")
            print(f"Trade Amount: ${self.trade_amount}")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error getting summary: {e}")

if __name__ == "__main__":
    monitor = RealTradingMonitor()
    
    try:
        monitor.monitor_and_trade()
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        monitor.stop_monitoring()
        monitor.get_trading_summary()