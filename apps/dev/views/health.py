"""Vistas de salud del servidor."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from ..decorators import dev_profile_required
from ..models import DevLog, DevPingLog
from ..services import get_server_health, record_health_log


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def health_dashboard(request):
    """Dashboard de salud del servidor."""
    health = get_server_health()

    if request.method == 'POST':
        record_health_log()
        health = get_server_health()

    recent_logs = DevLog.objects.all()[:20]
    recent_pings = DevPingLog.objects.all()[:20]

    context = {
        'health': health,
        'recent_logs': recent_logs,
        'recent_pings': recent_pings,
    }
    return render(request, 'dev/health/health_dashboard.html', context)
