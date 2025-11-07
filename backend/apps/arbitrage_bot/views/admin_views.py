# backend/apps/arbitrage_bot/admin_views.py
# Admin-specific views can go here
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

@staff_member_required
def admin_system_overview(request):
    """Admin-only system overview"""
    # Add admin-specific functionality here
    return JsonResponse({'status': 'admin_view'})