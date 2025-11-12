# backend/core/websocket.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .authentication import WebSocketJWTAuthentication

User = get_user_model()

class BaseWebSocketConsumer(AsyncWebsocketConsumer):
    """
    Base WebSocket consumer with authentication and common functionality.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.group_name = None
        self.authenticator = WebSocketJWTAuthentication()
    
    async def connect(self):
        """
        Handle WebSocket connection with authentication.
        """
        try:
            # Authenticate user
            auth_result = await sync_to_async(self.authenticator.authenticate)(self.scope)
            
            if auth_result:
                self.user, _ = auth_result
                self.scope['user'] = self.user
                
                # Generate group name based on user ID
                self.group_name = f"user_{self.user.id}"
                
                # Add to user group
                await self.channel_layer.group_add(
                    self.group_name,
                    self.channel_name
                )
                
                await self.accept()
                
                # Send connection confirmation
                await self.send(text_data=json.dumps({
                    'type': 'connection_established',
                    'message': 'WebSocket connection established',
                    'user_id': self.user.id
                }))
                
                # Log connection
                await self.on_connected()
            else:
                await self.close(code=4001)  # Unauthorized
                
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await self.close(code=4000)  # Internal error
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if self.group_name:
            # Remove from user group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        
        await self.on_disconnected(close_code)
    
    async def on_connected(self):
        """
        Override in subclasses to handle connection events.
        """
        pass
    
    async def on_disconnected(self, close_code):
        """
        Override in subclasses to handle disconnection events.
        """
        pass
    
    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        """
        try:
            data = json.loads(text_data)
            await self.handle_message(data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_message(self, data):
        """
        Handle incoming WebSocket messages. Override in subclasses.
        """
        message_type = data.get('type')
        
        if message_type == 'ping':
            await self.send_pong()
        else:
            await self.send_error(f"Unknown message type: {message_type}")
    
    async def send_pong(self):
        """
        Respond to ping messages.
        """
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': self.get_current_timestamp()
        }))
    
    async def send_error(self, message):
        """
        Send error message to client.
        """
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': self.get_current_timestamp()
        }))
    
    async def send_message(self, message_type, data):
        """
        Send message to client.
        """
        message = {
            'type': message_type,
            'data': data,
            'timestamp': self.get_current_timestamp()
        }
        await self.send(text_data=json.dumps(message))
    
    async def broadcast_to_group(self, group, message_type, data):
        """
        Broadcast message to a group.
        """
        await self.channel_layer.group_send(
            group,
            {
                'type': 'group_message',
                'message_type': message_type,
                'data': data
            }
        )
    
    async def group_message(self, event):
        """
        Handle messages sent to the group.
        """
        await self.send_message(
            event['message_type'],
            event['data']
        )
    
    def get_current_timestamp(self):
        """
        Get current timestamp in milliseconds.
        """
        import time
        return int(time.time() * 1000)

class ArbitrageConsumer(BaseWebSocketConsumer):
    """
    WebSocket consumer for real-time arbitrage opportunities.
    """
    
    async def on_connected(self):
        """
        Send initial arbitrage data when connected.
        """
        # Send recent opportunities
        opportunities = await self.get_recent_opportunities()
        await self.send_message('initial_opportunities', opportunities)
        
        # Subscribe to real-time updates
        await self.channel_layer.group_add(
            "arbitrage_updates",
            self.channel_name
        )
    
    async def on_disconnected(self, close_code):
        """
        Handle disconnection from arbitrage updates.
        """
        await self.channel_layer.group_discard(
            "arbitrage_updates",
            self.channel_name
        )
    
    async def handle_message(self, data):
        """
        Handle arbitrage-specific messages.
        """
        message_type = data.get('type')
        
        if message_type == 'subscribe_symbol':
            symbol = data.get('symbol')
            await self.subscribe_to_symbol(symbol)
        elif message_type == 'unsubscribe_symbol':
            symbol = data.get('symbol')
            await self.unsubscribe_from_symbol(symbol)
        else:
            await super().handle_message(data)
    
    async def subscribe_to_symbol(self, symbol):
        """
        Subscribe to updates for a specific symbol.
        """
        group_name = f"symbol_{symbol}"
        await self.channel_layer.group_add(
            group_name,
            self.channel_name
        )
        
        await self.send_message('subscription_confirmed', {
            'symbol': symbol,
            'message': f"Subscribed to {symbol} updates"
        })
    
    async def unsubscribe_from_symbol(self, symbol):
        """
        Unsubscribe from updates for a specific symbol.
        """
        group_name = f"symbol_{symbol}"
        await self.channel_layer.group_discard(
            group_name,
            self.channel_name
        )
    
    @database_sync_to_async
    def get_recent_opportunities(self):
        """
        Get recent arbitrage opportunities from database.
        """
        from apps.arbitrage.models import ArbitrageOpportunity
        
        opportunities = ArbitrageOpportunity.objects.filter(
            status='active'
        ).order_by('-detected_at')[:10]
        
        return [
            {
                'id': opp.id,
                'symbol': opp.symbol,
                'buy_exchange': opp.buy_exchange.name,
                'sell_exchange': opp.sell_exchange.name,
                'profit_percentage': float(opp.profit_percentage),
                'detected_at': opp.detected_at.isoformat()
            }
            for opp in opportunities
        ]

class TradingConsumer(BaseWebSocketConsumer):
    """
    WebSocket consumer for real-time trading updates.
    """
    
    async def on_connected(self):
        """
        Send initial trading data when connected.
        """
        # Send recent trades
        trades = await self.get_recent_trades()
        await self.send_message('initial_trades', trades)
        
        # Send current positions
        positions = await self.get_current_positions()
        await self.send_message('current_positions', positions)
    
    async def handle_message(self, data):
        """
        Handle trading-specific messages.
        """
        message_type = data.get('type')
        
        if message_type == 'place_order':
            await self.place_order(data)
        elif message_type == 'cancel_order':
            order_id = data.get('order_id')
            await self.cancel_order(order_id)
        else:
            await super().handle_message(data)
    
    async def place_order(self, data):
        """
        Place a new order through WebSocket.
        """
        try:
            # Validate order data
            validated_data = await self.validate_order_data(data)
            
            # Place order (this would be an async call to your trading service)
            order_result = await self.execute_place_order(validated_data)
            
            await self.send_message('order_placed', order_result)
            
        except Exception as e:
            await self.send_error(f"Failed to place order: {str(e)}")
    
    async def cancel_order(self, order_id):
        """
        Cancel an existing order.
        """
        try:
            # Cancel order (async call to trading service)
            cancel_result = await self.execute_cancel_order(order_id)
            
            await self.send_message('order_cancelled', cancel_result)
            
        except Exception as e:
            await self.send_error(f"Failed to cancel order: {str(e)}")
    
    @database_sync_to_async
    def get_recent_trades(self):
        """
        Get recent trades for the user.
        """
        from apps.trading.models import TradeExecution
        
        trades = TradeExecution.objects.filter(
            user=self.user
        ).order_by('-created_at')[:20]
        
        return [
            {
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'amount': float(trade.amount),
                'price': float(trade.price),
                'status': trade.status,
                'created_at': trade.created_at.isoformat()
            }
            for trade in trades
        ]
    
    @database_sync_to_async
    def get_current_positions(self):
        """
        Get current positions for the user.
        """
        # This would depend on your position tracking implementation
        return []
    
    async def validate_order_data(self, data):
        """
        Validate order data before placement.
        """
        # Implement order validation logic
        required_fields = ['symbol', 'side', 'amount', 'order_type']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return data
    
    async def execute_place_order(self, data):
        """
        Execute order placement (to be implemented with actual trading logic).
        """
        # Placeholder implementation
        return {
            'order_id': 'temp_order_id',
            'status': 'pending',
            'message': 'Order received and being processed'
        }
    
    async def execute_cancel_order(self, order_id):
        """
        Execute order cancellation (to be implemented).
        """
        # Placeholder implementation
        return {
            'order_id': order_id,
            'status': 'cancelled',
            'message': 'Order cancellation requested'
        }

# WebSocket routing configuration
from django.urls import re_path
from channels.routing import URLRouter

websocket_urlpatterns = [
    re_path(r'ws/arbitrage/$', ArbitrageConsumer.as_asgi()),
    re_path(r'ws/trading/$', TradingConsumer.as_asgi()),
]