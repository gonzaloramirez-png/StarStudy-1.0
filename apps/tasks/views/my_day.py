"""Vista Mi Día: Kanban diario del estudiante.

- my_day: panel kanban con tareas organizadas por prioridad
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count

from apps.tasks.models import Task


@login_required
def my_day(request):
    """Panel Mi Día - Kanban diario con 3 columnas: Urgente, Esta semana, Largo plazo."""
    user = request.user
    now = timezone.now()
    today = now.date()
    week_end = today + timedelta(days=7)

    # Tareas base (no personales, asignadas al usuario)
    base_tasks = Task.objects.filter(
        assigned_to=user,
        is_personal=False,
    ).select_related('assigned_to', 'assigned_by', 'course').order_by('deadline')

    # === URGENTE (vencidas hoy, o vencen en ≤3 días, o importancia HIGH/CRITICAL) ===
    urgent = base_tasks.filter(
        Q(deadline__date__lte=today) |
        Q(deadline__date__lte=today + timedelta(days=3), importance__in=['HIGH', 'CRITICAL']) |
        Q(importance='CRITICAL')
    ).filter(is_completed=False).distinct()[:10]

    # === ESTA SEMANA (vencen en ≤7 días, no urgentes) ===
    this_week = base_tasks.filter(
        deadline__date__gt=today,
        deadline__date__lte=week_end,
        is_completed=False,
        importance__in=['LOW', 'MEDIUM', 'HIGH'],
    ).exclude(pk__in=urgent.values_list('pk', flat=True)).distinct()[:10]

    # === LARGO PLAZO (vencen después de 7 días) ===
    long_term = base_tasks.filter(
        deadline__date__gt=week_end,
        is_completed=False,
    ).distinct()[:10]

    # === COMPLETADAS HOY ===
    completed_today = base_tasks.filter(
        is_completed=True,
        completed_at__date=today,
    ).order_by('-completed_at')[:10]

    # Stats del día
    total_pending = base_tasks.filter(is_completed=False).count()
    overdue_count = base_tasks.filter(is_completed=False, deadline__date__lt=today).count()
    completed_count = base_tasks.filter(is_completed=True, completed_at__date=today).count()

    # XP ganada hoy (de tareas completadas)
    today_tasks = base_tasks.filter(is_completed=True, completed_at__date=today)
    xp_today = sum(round(t.score * 0.25) if t.score else 0 for t in today_tasks)

    context = {
        'urgent': urgent,
        'this_week': this_week,
        'long_term': long_term,
        'completed_today': completed_today,
        'total_pending': total_pending,
        'overdue_count': overdue_count,
        'completed_count': completed_count,
        'xp_today': xp_today,
        'today': today,
        'now': now,
    }
    return render(request, 'tasks/my_day.html', context)
