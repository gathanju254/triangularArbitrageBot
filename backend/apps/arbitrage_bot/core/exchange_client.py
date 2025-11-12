# backend/apps/arbitrage_bot/core/exchange_client.py

import logging
from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.exchanges.api_key_integration import exchange_api_integration
from apps.exchanges.services import ExchangeFactory

logger = logging.getLogger(__name__)
User = get_user_model()


class ArbitrageExchangeClient:
    """
    Exchange client for arbitrage bot that uses database API keys.
    """
    
    def __init__(self, user_id: int = None):
        self.user = None
        if user_id:
            try:
                self.user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found, using public connectors")
    
    def get_authenticated_connector(self, exchange_code: str):
        """
        Get authenticated exchange connector for trading.
        """
        if not self.user:
            logger.warning(f"No user provided, creating public connector for {exchange_code}")
            return exchange_api_integration._create_public_connector(exchange_code)
        
        return exchange_api_integration.create_exchange_connector(
            user=self.user,
            exchange_code=exchange_code
        )
    
    def get_balance(self, exchange_code: str) -> Dict:
        """
        Get balance for an exchange using user's API keys.
        """
        try:
            if not self.user:
                return {'error': 'User required for balance check'}
            
            exchange_service = ExchangeFactory.get_exchange_by_code(
                exchange_code, 
                user=self.user
            )
            
            return exchange_service.get_user_balance()
            
        except Exception as e:
            logger.error(f"Failed to get balance for {exchange_code}: {e}")
            return {'error': str(e)}
    
    def get_all_balances(self) -> Dict[str, Dict]:
        """
        Get balances across all user's configured exchanges.
        """
        if not self.user:
            return {'error': 'User required for balance check'}
        
        try:
            exchange_services = ExchangeFactory.get_user_exchanges_with_keys(self.user)
            balances = {}
            
            for exchange_service in exchange_services:
                try:
                    balance_info = exchange_service.get_user_balance()
                    balances[exchange_service.exchange.code] = balance_info
                except Exception as e:
                    logger.error(f"Failed to get balance for {exchange_service.exchange.name}: {e}")
                    continue
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get all balances: {e}")
            return {'error': str(e)}
    
    def execute_trade(self, exchange_code: str, symbol: str, side: str, 
                     order_type: str, amount: float, price: float = None) -> Dict:
        """
        Execute a trade using user's API keys.
        """
        try:
            connector = self.get_authenticated_connector(exchange_code)
            if not connector or not connector.api_key:
                return {
                    'status': 'failed',
                    'error': f'No authenticated connector available for {exchange_code}'
                }
            
            # Execute the order
            order_result = connector.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                amount=amount,
                price=price
            )
            
            return {
                'status': 'executed',
                'order_id': order_result.get('id'),
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'exchange': exchange_code,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'exchange': exchange_code,
                'timestamp': timezone.now().isoformat()
            }