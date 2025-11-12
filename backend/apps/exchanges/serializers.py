# backend/apps/exchanges/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Exchange, MarketData, ExchangeCredentials
from apps.users.serializers import UserSerializer, APIKeySerializer


class ExchangeSerializer(serializers.ModelSerializer):
    """Serializer for Exchange model"""
    
    exchange_type_display = serializers.CharField(
        source='get_exchange_type_display', 
        read_only=True
    )
    supported_pairs_count = serializers.SerializerMethodField()
    is_configured = serializers.SerializerMethodField()
    
    class Meta:
        model = Exchange
        fields = [
            'id', 'name', 'code', 'exchange_type', 'exchange_type_display',
            'base_url', 'api_documentation', 'is_active', 'trading_fee',
            'withdrawal_fee', 'rate_limit', 'precision_info', 
            'supported_pairs', 'supported_pairs_count', 'is_configured',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_supported_pairs_count(self, obj):
        """Get count of supported pairs"""
        return len(obj.supported_pairs) if obj.supported_pairs else 0
    
    def get_is_configured(self, obj):
        """Check if user has configured this exchange"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ExchangeCredentials.objects.filter(
                user=request.user, 
                exchange=obj,
                is_validated=True
            ).exists()
        return False


class MarketDataSerializer(serializers.ModelSerializer):
    """Serializer for MarketData model"""
    
    exchange = ExchangeSerializer(read_only=True)
    age_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketData
        fields = [
            'id', 'exchange', 'symbol', 'bid_price', 'ask_price', 
            'last_price', 'volume_24h', 'spread', 'timestamp', 
            'is_fresh', 'age_seconds'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_age_seconds(self, obj):
        """Calculate data age in seconds"""
        return (timezone.now() - obj.timestamp).total_seconds()


class ExchangeCredentialsSerializer(serializers.ModelSerializer):
    """Serializer for ExchangeCredentials model"""
    
    user = UserSerializer(read_only=True)
    exchange = ExchangeSerializer(read_only=True)
    api_key = APIKeySerializer(read_only=True)
    
    class Meta:
        model = ExchangeCredentials
        fields = [
            'id', 'user', 'exchange', 'api_key', 'is_validated',
            'validation_message', 'last_validation', 'trading_enabled',
            'withdrawal_enabled'
        ]
        read_only_fields = [
            'id', 'user', 'is_validated', 'validation_message', 
            'last_validation'
        ]


class CreateExchangeCredentialsSerializer(serializers.ModelSerializer):
    """Serializer for creating exchange credentials"""
    
    api_key_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ExchangeCredentials
        fields = ['exchange', 'api_key_id', 'trading_enabled', 'withdrawal_enabled']
    
    def validate(self, data):
        """Validate credentials data"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Check if credentials already exist for this user and exchange
            existing = ExchangeCredentials.objects.filter(
                user=request.user,
                exchange=data['exchange']
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    "Credentials already exist for this exchange"
                )
            
            # Verify API key belongs to user
            from apps.users.models import APIKey
            try:
                api_key = APIKey.objects.get(
                    id=data['api_key_id'],
                    user=request.user
                )
                data['api_key'] = api_key
            except APIKey.DoesNotExist:
                raise serializers.ValidationError("Invalid API key")
        
        return data
    
    def create(self, validated_data):
        """Create exchange credentials"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        # Remove api_key_id as it's not a model field
        validated_data.pop('api_key_id', None)
        
        return super().create(validated_data)


class ExchangeBalanceSerializer(serializers.Serializer):
    """Serializer for exchange balance information"""
    
    exchange = ExchangeSerializer(read_only=True)
    balances = serializers.DictField(
        child=serializers.DecimalField(max_digits=20, decimal_places=8)
    )
    total_balance_usd = serializers.DecimalField(max_digits=15, decimal_places=2)
    last_updated = serializers.DateTimeField()


class TickerSerializer(serializers.Serializer):
    """Serializer for ticker data"""
    
    symbol = serializers.CharField()
    exchange = serializers.CharField()
    bid_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    ask_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    last_price = serializers.DecimalField(max_digits=20, decimal_places=8)
    volume_24h = serializers.DecimalField(max_digits=20, decimal_places=8)
    price_change_24h = serializers.DecimalField(max_digits=10, decimal_places=4)
    spread = serializers.DecimalField(max_digits=10, decimal_places=4)
    timestamp = serializers.DateTimeField()


class OrderBookSerializer(serializers.Serializer):
    """Serializer for order book data"""
    
    symbol = serializers.CharField()
    exchange = serializers.CharField()
    bids = serializers.ListField(
        child=serializers.ListField(
            child=serializers.DecimalField(max_digits=20, decimal_places=8),
            min_length=2,
            max_length=2
        )
    )
    asks = serializers.ListField(
        child=serializers.ListField(
            child=serializers.DecimalField(max_digits=20, decimal_places=8),
            min_length=2,
            max_length=2
        )
    )
    timestamp = serializers.DateTimeField()


class ExchangeStatusSerializer(serializers.Serializer):
    """Serializer for exchange status"""
    
    exchange = ExchangeSerializer(read_only=True)
    is_online = serializers.BooleanField()
    last_checked = serializers.DateTimeField()
    response_time_ms = serializers.IntegerField()
    maintenance_mode = serializers.BooleanField()
    message = serializers.CharField(required=False)


class TradingPairSerializer(serializers.Serializer):
    """Serializer for trading pair information"""
    
    symbol = serializers.CharField()
    base_asset = serializers.CharField()
    quote_asset = serializers.CharField()
    min_order_size = serializers.DecimalField(max_digits=15, decimal_places=8)
    max_order_size = serializers.DecimalField(max_digits=15, decimal_places=8)
    price_precision = serializers.IntegerField()
    amount_precision = serializers.IntegerField()
    is_active = serializers.BooleanField()