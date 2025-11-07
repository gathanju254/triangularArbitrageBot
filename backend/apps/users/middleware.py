# backend/apps/users/middleware.py
import logging
from typing import Callable

from django.utils import timezone

logger = logging.getLogger(__name__)


class UserTimezoneMiddleware:
    """
    Attach user's timezone to the request and activate it for the duration
    of the request if available. Non-breaking if user/profile is missing.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):
        tz = None
        try:
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                # Prefer explicit user.timezone, fallback to profile.timezone
                tz = getattr(user, "timezone", None) or getattr(getattr(user, "profile", None), "timezone", None)
                if tz:
                    try:
                        timezone.activate(tz)
                        request.user_timezone = tz
                    except Exception:
                        logger.debug(f"Invalid timezone '{tz}' for user {getattr(user,'username',None)}", exc_info=True)
                        request.user_timezone = None
                else:
                    request.user_timezone = None
            else:
                request.user_timezone = None
        except Exception:
            # Don't allow middleware errors to break request processing
            logger.exception("Error in UserTimezoneMiddleware")
            request.user_timezone = None

        response = self.get_response(request)

        # Deactivate timezone after response
        try:
            timezone.deactivate()
        except Exception:
            pass

        return response
