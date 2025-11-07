# backend/apps/users/urls/__init__.py
from .api_urls import urlpatterns as api_urls
from .web_urls import urlpatterns as web_urls
from .admin_urls import urlpatterns as admin_urls

urlpatterns = api_urls + web_urls + admin_urls 

__all__ = ['api_urls', 'web_urls', 'admin_urls', 'urlpatterns']