# Import URL patterns to make them accessible
from .api_urls import urlpatterns as api_urlpatterns
from .admin_urls import urlpatterns as admin_urlpatterns  
from .web_urls import urlpatterns as web_urlpatterns

# Combine all URL patterns
urlpatterns = api_urlpatterns + admin_urlpatterns + web_urlpatterns