"""Vista de Pomodoro: temporizador de estudio con XP."""
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
def pomodoro(request):
    """Página del temporizador Pomodoro."""
    return render(request, 'accounts/pomodoro.html')


@login_required
@require_POST
def pomodoro_save(request):
    """Guarda una sesión de Pomodoro y otorga XP."""
    try:
        data = json.loads(request.body)
        xp = min(int(data.get('xp', 10)), 50)  # Max 50 XP por sesión
    except (ValueError, TypeError, json.JSONDecodeError):
        xp = 10

    request.user.add_xp(xp, source='Pomodoro session')

    # Registrar actividad para streaks
    from apps.accounts.models import UserActivity
    UserActivity.record_activity(request.user, 'task')

    return JsonResponse({
        'success': True,
        'xp_earned': xp,
        'total_xp': request.user.xp,
        'level': request.user.level,
    })
