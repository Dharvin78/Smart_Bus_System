from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from .models import AuditLog


@login_required
def audit_list(request):

    logs = AuditLog.objects.select_related("user").all()

    search = request.GET.get("search")
    module = request.GET.get("module")
    action = request.GET.get("action")

    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(description__icontains=search)
        )

    if module:
        logs = logs.filter(module=module)

    if action:
        logs = logs.filter(action=action)

    paginator = Paginator(logs, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "modules": AuditLog.objects.values_list(
            "module",
            flat=True
        ).distinct(),
        "actions": AuditLog.ACTION_CHOICES,
    }

    return render(
        request,
        "audit/audit_list.html",
        context
    )