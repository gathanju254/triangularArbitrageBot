# backend/apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, APIKey

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_verified', 'created_at')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Tudollar Info', {
            'fields': ('user_type', 'phone', 'timezone', 'is_verified')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Tudollar Info', {
            'fields': ('user_type', 'phone', 'timezone')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'risk_tolerance', 'max_daily_loss', 'max_position_size')
    list_filter = ('risk_tolerance',)
    search_fields = ('user__username', 'user__email')

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'exchange', 'is_active', 'is_encrypted', 'created_at')
    list_filter = ('exchange', 'is_active', 'is_encrypted')
    search_fields = ('user__username', 'exchange')
    readonly_fields = ('created_at', 'last_used')