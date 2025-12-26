import time
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from apps.accounts.utils import perform_logout


class InactivityLogoutMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # You are using session-based auth, not request.user
        if "user_id" not in request.session:
            return

        now = int(time.time())
        last_activity = request.session.get("last_activity")

        if last_activity:
            inactive_seconds = now - last_activity

            if inactive_seconds > settings.SESSION_INACTIVITY_TIMEOUT:
                # ✅ Single source of truth
                perform_logout(request)
                return

        # Update activity timestamp
        request.session["last_activity"] = now
