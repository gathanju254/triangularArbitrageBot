# backend/apps/risk_management/engines/position_sizer.py
from decimal import Decimal

class PositionSizer:
    def __init__(self, risk_config):
        self.risk_config = risk_config

    def calculate_position_size(self, current_price, volatility_factor=1.0):
        """Calculate optimal position size based on risk parameters"""
        # Calculate based on maximum position size
        max_position_usd = self.risk_config.max_position_size_usd
        
        # Calculate based on maximum percentage of portfolio
        # This would typically use the user's portfolio value
        portfolio_value = self._get_portfolio_value()
        max_position_percentage = self.risk_config.max_position_percentage / Decimal('100.0')
        max_position_by_percentage = portfolio_value * max_position_percentage
        
        # Use the more conservative limit
        max_position = min(max_position_usd, max_position_by_percentage)
        
        # Adjust for volatility
        volatility_adjustment = Decimal('1.0') / volatility_factor
        adjusted_position = max_position * volatility_adjustment
        
        # Calculate quantity based on current price
        if current_price > 0:
            quantity = adjusted_position / current_price
        else:
            quantity = Decimal('0')
            
        return max(quantity, Decimal('0'))

    def calculate_stop_loss(self, entry_price, risk_per_trade=0.01):
        """Calculate stop loss price based on risk parameters"""
        # risk_per_trade is the percentage of portfolio risked per trade
        portfolio_value = self._get_portfolio_value()
        risk_amount = portfolio_value * Decimal(str(risk_per_trade))
        
        position_size = self.calculate_position_size(entry_price)
        if position_size > 0:
            stop_loss_distance = risk_amount / position_size
            stop_loss_price = entry_price - stop_loss_distance
            return max(stop_loss_price, Decimal('0'))
        
        return entry_price

    def _get_portfolio_value(self):
        """Get user's portfolio value (simplified implementation)"""
        # In a real implementation, this would fetch from portfolio service
        return Decimal('10000.00')  # Default portfolio value