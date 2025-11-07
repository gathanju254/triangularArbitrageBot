# backend/apps/arbitrage_bot/views/web_views.py

# Web/HTML views can go here
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    """Main dashboard view"""
    return render(request, 'arbitrage_bot/dashboard.html')

@login_required
def trading_view(request):
    """Trading interface view"""
    return render(request, 'arbitrage_bot/trading.html')

@login_required
def settings_view(request):
    """Settings interface view"""
    return render(request, 'arbitrage_bot/settings.html')

@login_required
def analytics_view(request):
    """Analytics and performance view"""
    return render(request, 'arbitrage_bot/analytics.html')