"""Vistas para alertas push en el navegador.

- push_status: endpoint JSON con datos para disparar notificaciones nativas
  (tareas urgentes y hábitos de hoy). Se consulta desde notifications.js.
- service_worker: sirve el Service Worker desde la raíz del sitio para poder
  manejar los clics en las notificaciones.
"""
import json
from pathlib import Path
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from apps.tasks.models import Task


@login_required
def push_status(request):
    user = request.user

    prefs = getattr(user, 'notification_preferences', None)
    if prefs is not None and not prefs.push:
        return JsonResponse({'urgent': [], 'habits': [], 'push_enabled': False})

    now = timezone.now()
    urgent_date = now + timedelta(days=3)

    if user.role in ('TEACHER', 'STAFF', 'PROGRAMMER'):
        tasks = Task.objects.filter(
            assigned_by=user,
            is_personal=False,
            is_completed=False,
            importance__in=['HIGH', 'CRITICAL'],
            deadline__lte=urgent_date,
        ).only('pk', 'title', 'deadline')
    else:
        tasks = Task.objects.filter(
            assigned_to=user,
            is_personal=False,
            is_completed=False,
            importance__in=['HIGH', 'CRITICAL'],
            deadline__lte=urgent_date,
        ).only('pk', 'title', 'deadline')

    urgent = [
        {'pk': t.pk, 'title': t.title, 'deadline': t.deadline.strftime('%d/%m %H:%M')}
        for t in tasks[:5]
    ]

    habits = []
    if user.role == 'STAFF':
        today = timezone.localdate()
        for h in user.habits.all().only('pk', 'title', 'start_time', 'end_time'):
            if h.start_time is None or (h.start_time.hour == 0 and h.start_time.minute == 0):
                continue
            habits.append({
                'pk': h.pk,
                'title': h.title,
                'start_time': h.start_time.strftime('%H:%M'),
                'end_time': h.end_time.strftime('%H:%M'),
            })

    return JsonResponse({
        'urgent': urgent,
        'habits': habits,
        'push_enabled': True,
    })


def service_worker(request):
    sw_path = Path(__file__).resolve().parent.parent.parent.parent / 'static' / 'js' / 'sw.js'
    if not sw_path.exists():
        raise Http404
    return HttpResponse(
        sw_path.read_text(encoding='utf-8'),
        content_type='application/javascript; charset=utf-8',
    )
