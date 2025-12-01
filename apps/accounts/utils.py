# apps/accounts/utils.py
from django.utils import timezone
from apps.accounts.models import AuditTrail

def perform_logout(request):
    """
    Handles manual or auto logout.
    Updates last_seen and creates logout record.
    """
    now = timezone.now()
    
    if "user_id" in request.session:
        user_id = request.session.get("user_id")
        user_name = request.session.get("user_name", "")
        role_name = request.session.get("role_name", "")
        audit_id = request.session.get("audit_id")

        # Update last_seen before logout
        if audit_id:
            AuditTrail.objects.filter(id=audit_id, action="login").update(last_seen=now)

        # Create logout record
        AuditTrail.objects.create(
            user_id=user_id,
            user_name=user_name,
            role_name=role_name,
            action="logout",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:255],
            timestamp=now,
        )

    request.session.flush()

