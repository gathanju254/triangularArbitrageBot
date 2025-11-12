# backend/apps/users/serializers/serializers.py

import logging
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import User, UserProfile, APIKey
from ..services import APIKeyService

logger = logging.getLogger(__name__)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'risk_tolerance', 
            'max_daily_loss', 
            'max_position_size',
            'preferred_exchanges', 
            'notification_preferences'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_max_daily_loss(self, value):
        """Validate max daily loss is positive"""
        if value <= 0:
            raise serializers.ValidationError("Max daily loss must be positive")
        return value
    
    def validate_max_position_size(self, value):
        """Validate max position size is positive"""
        if value <= 0:
            raise serializers.ValidationError("Max position size must be positive")
        return value


class APIKeySerializer(serializers.ModelSerializer):
    """Basic API key serializer for listing"""
    
    exchange_display = serializers.CharField(source='get_exchange_display', read_only=True)
    is_usable = serializers.BooleanField(read_only=True)
    requires_passphrase = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = [
            'id', 
            'exchange', 
            'exchange_display',
            'label', 
            'is_active', 
            'is_validated',
            'is_usable',
            'requires_passphrase',
            'created_at', 
            'last_used',
            'last_validated'
        ]
        read_only_fields = [
            'id', 
            'created_at', 
            'last_used', 
            'last_validated',
            'is_validated'
        ]


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating API keys with enhanced validation"""
    
    class Meta:
        model = APIKey
        fields = [
            'exchange', 'label', 'api_key', 'secret_key', 'passphrase',
            'is_active', 'permissions'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True},
            'secret_key': {'write_only': True},
            'passphrase': {'write_only': True, 'required': False, 'allow_blank': True}
        }

    def validate(self, data):
        """Enhanced validation for API key creation"""
        exchange = data.get('exchange')
        api_key = data.get('api_key')
        secret_key = data.get('secret_key')
        passphrase = data.get('passphrase', '')

        if not exchange or not api_key or not secret_key:
            raise serializers.ValidationError("Exchange, api_key and secret_key are required")

        # Validate exchange-specific requirements
        ex_lower = exchange.lower()
        if ex_lower == 'okx':
            if not passphrase:
                raise serializers.ValidationError({
                    'passphrase': 'OKX requires a passphrase for API authentication'
                })
            
            if api_key and len(api_key.strip()) < 20:
                raise serializers.ValidationError({
                    'api_key': 'OKX API key appears to be too short'
                })
            
            if secret_key and len(secret_key.strip()) < 20:
                raise serializers.ValidationError({
                    'secret_key': 'OKX secret key appears to be too short'
                })

        elif ex_lower in ['coinbase', 'kucoin']:
            if not passphrase:
                raise serializers.ValidationError({
                    'passphrase': f'{exchange} requires a passphrase for API authentication'
                })

        return data

    def create(self, validated_data):
        """Create API key with automatic encryption"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        # Set default permissions if not provided
        if 'permissions' not in validated_data or not validated_data['permissions']:
            validated_data['permissions'] = ['read', 'trade']

        # Create the API key instance (do not save before encryption)
        api_key = APIKey(**validated_data)
        
        # Encrypt the keys before saving using model helper
        try:
            api_key.encrypt_keys(use_legacy_prefix=False)
        except Exception as e:
            logger.error(f"Encryption failed during API key creation: {e}")
            raise serializers.ValidationError({
                'non_field_errors': f'Failed to secure API keys: {str(e)}'
            })

        api_key.save()
        return api_key


class APIKeyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for API key with comprehensive information"""
    
    exchange_display = serializers.CharField(source='get_exchange_display', read_only=True)
    passphrase_set = serializers.BooleanField(source='requires_passphrase', read_only=True)
    is_usable = serializers.BooleanField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = [
            'id', 
            'exchange', 
            'exchange_display',
            'label', 
            'display_name',
            'is_active', 
            'is_validated',
            'is_encrypted',
            'is_usable',
            'passphrase_set',
            'created_at', 
            'updated_at',
            'last_used',
            'last_validated'
        ]
        read_only_fields = [
            'id', 
            'created_at', 
            'updated_at',
            'last_used', 
            'last_validated',
            'is_validated',
            'is_encrypted'
        ]


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating API keys with proper partial update handling"""
    
    class Meta:
        model = APIKey
        fields = ['label', 'api_key', 'secret_key', 'passphrase', 'is_active']
        extra_kwargs = {
            'api_key': {'write_only': True, 'required': False},
            'secret_key': {'write_only': True, 'required': False},
            'passphrase': {'write_only': True, 'required': False, 'allow_blank': True},
            'is_active': {'required': False},
            'label': {'required': False, 'allow_blank': True}
        }

    def update(self, instance, validated_data):
        logger.info(f"🔄 Updating API key {instance.id} for {instance.exchange}...")
        
        # Only update fields that were actually provided
        if 'api_key' in validated_data:
            instance.api_key = validated_data['api_key']
            instance.is_encrypted = False  # Force re-encryption
        
        if 'secret_key' in validated_data:
            instance.secret_key = validated_data['secret_key']
            instance.is_encrypted = False
        
        if 'passphrase' in validated_data:
            instance.passphrase = validated_data['passphrase']
            instance.is_encrypted = False
        
        if 'label' in validated_data:
            instance.label = validated_data['label']
        
        if 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']

        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(
        write_only=True, 
        validators=[validate_password],
        help_text='Password must meet security requirements'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text='Confirm your password'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 
            'email', 
            'password', 
            'password_confirm', 
            'first_name', 
            'last_name', 
            'phone', 
            'timezone'
        ]
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
            'timezone': {'required': False},
        }
    
    def validate(self, attrs):
        """Validate registration data"""
        logger.info("🔧 Validating user registration data")
        
        if attrs['password'] != attrs['password_confirm']:
            logger.warning("❌ Password confirmation failed")
            raise serializers.ValidationError({
                "password_confirm": "Passwords don't match"
            })
        
        # Check if username or email already exists
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({
                "username": "A user with this username already exists"
            })
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                "email": "A user with this email already exists"
            })
        
        logger.info("✅ Registration validation passed")
        return attrs
    
    def create(self, validated_data):
        """Create user and associated profile"""
        logger.info("🔧 Creating new user account")
        
        validated_data.pop('password_confirm')
        
        try:
            user = User.objects.create_user(**validated_data)
            logger.info(f"✅ User created successfully: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"❌ User creation failed: {e}")
            raise serializers.ValidationError("Failed to create user account")


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    profile = UserProfileSerializer(read_only=True)
    api_keys = APIKeySerializer(many=True, read_only=True)
    api_key_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'user_type', 
            'phone', 
            'timezone', 
            'is_verified', 
            'profile', 
            'api_keys',
            'api_key_stats',
            'created_at',
            'last_login'
        ]
        read_only_fields = [
            'id', 
            'user_type', 
            'is_verified', 
            'created_at',
            'last_login'
        ]
    
    def get_api_key_stats(self, obj):
        """Get API key statistics for the user"""
        from ..services import APIKeyService
        return APIKeyService.get_user_api_key_stats(obj)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user data"""
    
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'phone', 
            'timezone', 
            'profile'
        ]
    
    def update(self, instance, validated_data):
        """Update user and profile data"""
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile if provided
        if profile_data and hasattr(instance, 'profile'):
            profile_serializer = UserProfileSerializer(
                instance.profile, 
                data=profile_data, 
                partial=True
            )
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                raise serializers.ValidationError({
                    'profile': profile_serializer.errors
                })
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(
        required=True,
        help_text='Your current password'
    )
    new_password = serializers.CharField(
        required=True, 
        validators=[validate_password],
        help_text='New password must meet security requirements'
    )
    new_password_confirm = serializers.CharField(
        required=True,
        help_text='Confirm your new password'
    )
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value
    
    def validate(self, attrs):
        """Validate password change data"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "Passwords don't match"
            })
        
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                "new_password": "New password must be different from current password"
            })
        
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField(
        required=True,
        help_text='Email address associated with your account'
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    token = serializers.CharField(
        required=True,
        help_text='Password reset token sent to your email'
    )
    new_password = serializers.CharField(
        required=True, 
        validators=[validate_password],
        help_text='New password must meet security requirements'
    )
    new_password_confirm = serializers.CharField(
        required=True,
        help_text='Confirm your new password'
    )
    
    def validate(self, attrs):
        """Validate password reset data"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "Passwords don't match"
            })
        return attrs


class APIKeyTestSerializer(serializers.Serializer):
    """Serializer for testing API key connectivity"""
    
    api_key_id = serializers.IntegerField(
        required=True,
        help_text='ID of the API key to test'
    )
    force_test = serializers.BooleanField(
        default=False,
        required=False,
        help_text='Force test even if recently tested'
    )
    
    def validate_api_key_id(self, value):
        """Validate that the API key exists and belongs to the user"""
        request = self.context.get('request')
        try:
            api_key = APIKey.objects.get(id=value, user=request.user)
            return value
        except APIKey.DoesNotExist:
            raise serializers.ValidationError("API key not found or access denied")


class ExchangeCredentialsSerializer(serializers.Serializer):
    """Serializer for exchange credentials validation"""
    
    exchange = serializers.ChoiceField(
        choices=APIKey.EXCHANGE_CHOICES,
        required=True,
        help_text='Exchange name'
    )
    api_key = serializers.CharField(
        required=True,
        help_text='API key from the exchange'
    )
    secret_key = serializers.CharField(
        required=True,
        help_text='Secret key from the exchange'
    )
    passphrase = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text='Passphrase (required for OKX, Coinbase, KuCoin)'
    )
    
    def validate(self, attrs):
        """Validate exchange credentials (robust to camelCase/snake_case payloads)"""
        # support alternate field names from frontend (apiKey, secret, secretKey, passPhrase)
        exchange = attrs.get('exchange') or attrs.get('exchange_code') or attrs.get('exchangeName')
        api_key = attrs.get('api_key') or attrs.get('apiKey')
        secret_key = attrs.get('secret_key') or attrs.get('secret') or attrs.get('secretKey')
        passphrase = attrs.get('passphrase') or attrs.get('passPhrase') or None

        errors = {}
        if not exchange:
            errors['exchange'] = 'Exchange is required'
        if not api_key or not str(api_key).strip():
            errors['api_key'] = 'API key is required'
        if not secret_key or not str(secret_key).strip():
            errors['secret_key'] = 'Secret key is required'
        if errors:
            raise serializers.ValidationError(errors)

        # normalize values back into attrs so validated_data contains consistent keys
        attrs['exchange'] = exchange
        attrs['api_key'] = api_key.strip()
        attrs['secret_key'] = secret_key.strip()
        attrs['passphrase'] = passphrase.strip() if passphrase else ''

        # Use service validation for format/requirements
        is_valid, validation_errors = APIKeyService.validate_api_key_data(
            exchange, attrs['api_key'], attrs['secret_key'], attrs['passphrase']
        )
        if not is_valid:
            # return structured validation errors
            raise serializers.ValidationError({'non_field_errors': validation_errors})

        return attrs


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""
    
    class Meta:
        model = UserProfile
        fields = [
            'risk_tolerance', 
            'max_daily_loss', 
            'max_position_size',
            'preferred_exchanges',
            'notification_preferences'
        ]


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup"""
    
    enable_2fa = serializers.BooleanField(
        required=True,
        help_text='Enable or disable two-factor authentication'
    )


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for 2FA verification"""
    
    token = serializers.CharField(
        required=True, 
        max_length=6,
        min_length=6,
        help_text='6-digit authentication code'
    )


class APIKeySummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for API key lists"""
    
    exchange_display = serializers.CharField(source='get_exchange_display', read_only=True)
    passphrase_set = serializers.BooleanField(source='requires_passphrase', read_only=True)
    is_usable = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = APIKey
        fields = [
            'id', 
            'exchange', 
            'exchange_display',
            'label',
            'is_active', 
            'is_validated',
            'is_usable',
            'passphrase_set',
            'created_at', 
            'last_used'
        ]
        read_only_fields = fields


class APIKeyValidationResultSerializer(serializers.Serializer):
    """Serializer for API key validation results"""
    
    connected = serializers.BooleanField()
    exchange = serializers.CharField()
    api_key_id = serializers.IntegerField()
    permissions = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    account_type = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField(required=False)
    cached = serializers.BooleanField(default=False)


class UserDashboardSerializer(serializers.ModelSerializer):
    """Serializer for user dashboard data"""
    
    profile = UserProfileSerializer(read_only=True)
    api_keys_count = serializers.SerializerMethodField()
    active_api_keys_count = serializers.SerializerMethodField()
    validated_api_keys_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'profile', 
            'api_keys_count', 
            'active_api_keys_count',
            'validated_api_keys_count',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_api_keys_count(self, obj):
        return obj.api_keys.count()
    
    def get_active_api_keys_count(self, obj):
        return obj.api_keys.filter(is_active=True).count()
    
    def get_validated_api_keys_count(self, obj):
        return obj.api_keys.filter(is_active=True, is_validated=True).count()


class APIKeyBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updating API keys"""
    
    api_key_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text='List of API key IDs to update'
    )
    is_active = serializers.BooleanField(
        required=True,
        help_text='New active status for the API keys'
    )
    
    def validate_api_key_ids(self, value):
        """Validate that all API keys exist and belong to the user"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")
        
        # Check if all API keys belong to the user
        user_api_keys = APIKey.objects.filter(user=request.user)
        valid_ids = set(user_api_keys.values_list('id', flat=True))
        
        invalid_ids = [api_key_id for api_key_id in value if api_key_id not in valid_ids]
        if invalid_ids:
            raise serializers.ValidationError(
                f"API keys not found or access denied: {invalid_ids}"
            )
        
        return value


class APIKeyExportSerializer(serializers.ModelSerializer):
    """Serializer for exporting API key data (without sensitive information)"""
    
    exchange_display = serializers.CharField(source='get_exchange_display', read_only=True)
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = APIKey
        fields = [
            'id',
            'exchange',
            'exchange_display',
            'label',
            'is_active',
            'is_validated',
            'status',
            'created_at',
            'last_used',
            'last_validated'
        ]
        read_only_fields = fields
    
    def get_status(self, obj):
        """Get human-readable status"""
        if not obj.is_active:
            return 'Inactive'
        elif obj.is_validated:
            return 'Active & Validated'
        else:
            return 'Active (Not Validated)'


class APIKeyBulkOperationSerializer(serializers.Serializer):
    """Serializer for bulk API key operations"""
    
    operations = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text='List of operations to perform'
    )
    
    def validate_operations(self, value):
        """Validate bulk operations"""
        valid_operations = ['update', 'toggle_active', 'validate']
        
        for i, operation in enumerate(value):
            op_type = operation.get('type')
            if op_type not in valid_operations:
                raise serializers.ValidationError(
                    f"Operation {i}: Invalid operation type '{op_type}'. "
                    f"Must be one of {valid_operations}"
                )
            
            if op_type in ['update', 'toggle_active', 'validate']:
                if 'api_key_id' not in operation:
                    raise serializers.ValidationError(
                        f"Operation {i}: 'api_key_id' is required for '{op_type}' operation"
                    )
        
        return value


class APIKeyRotationSerializer(serializers.Serializer):
    """Serializer for API key encryption rotation"""
    
    confirm = serializers.BooleanField(
        required=True,
        help_text='Confirm that you want to rotate encryption for all API keys'
    )
    
    def validate_confirm(self, value):
        """Validate confirmation"""
        if not value:
            raise serializers.ValidationError(
                "You must confirm the encryption rotation operation"
            )
        return value