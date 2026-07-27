from .models import AuditLog


def create_audit_log(request, module, action, description):
    """
    Create an audit log entry.
    """

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        module=module,
        action=action,
        description=description,
        ip_address=request.META.get("REMOTE_ADDR"),
    )