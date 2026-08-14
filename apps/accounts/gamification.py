"""Gamificación: rachas y logros (badges).

- current_streak: días consecutivos con al menos un hábito completado.
- check_badges: evalúa condiciones de desbloqueo y crea UserBadge (idempotente).
- get_badges: estado de logros del usuario (desbloqueados/bloqueados).

Las condiciones viven acá, mapeadas por el `code` del modelo Badge.
"""
from datetime import timedelta

from apps.accounts.models import Badge, UserBadge
from apps.habits.models import HabitCompletion
from apps.tasks.models import Task


def current_streak(user, today=None):
    """Días consecutivos con al menos un hábito completado.

    Si hoy todavía no se completó nada, la racha no se rompe hasta que
    termine el día (cuenta desde ayer).
    """
    from django.utils import timezone

    today = today or timezone.localdate()
    dates = set(
        HabitCompletion.objects.filter(habit__user=user).values_list('date', flat=True)
    )
    if today not in dates:
        today -= timedelta(days=1)
    streak = 0
    while today in dates:
        streak += 1
        today -= timedelta(days=1)
    return streak


def _all_habits_done_today(user):
    from django.utils import timezone

    today = timezone.localdate()
    habits = list(user.habits.all())
    if not habits:
        return False
    done = set(
        HabitCompletion.objects.filter(habit__user=user, date=today)
        .values_list('habit_id', flat=True)
    )
    return all(h.pk in done for h in habits)


def _conditions(user, completed_count, critical_count, streak):
    return {
        'first_task': completed_count >= 1,
        'ten_tasks': completed_count >= 10,
        'fifty_tasks': completed_count >= 50,
        'critical_task': critical_count >= 1,
        'streak_3': streak >= 3,
        'streak_7': streak >= 7,
        'streak_30': streak >= 30,
        'daily_full': _all_habits_done_today(user),
    }


def check_badges(user, completed_count=None, critical_count=None):
    """Evalúa logros y desbloquea los que correspondan (idempotente).

    Retorna la lista de badges recién desbloqueados (vacía si no hay nuevos).
    Se invoca al completar tareas y al marcar hábitos.
    """
    if completed_count is None:
        completed_count = Task.objects.filter(
            assigned_to=user, is_completed=True,
        ).count()
    if critical_count is None:
        critical_count = Task.objects.filter(
            assigned_to=user, is_completed=True,
            importance=Task.Importance.CRITICAL,
        ).count()
    streak = current_streak(user)
    conditions = _conditions(user, completed_count, critical_count, streak)

    badges_by_code = {
        b.code: b
        for b in Badge.objects.filter(code__in=conditions.keys())
    }
    unlocked = []
    for code, meets in conditions.items():
        badge = badges_by_code.get(code)
        if badge and meets:
            _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
            if created:
                unlocked.append(badge)
    return unlocked


def get_badges(user):
    """Retorna (desbloqueados, bloqueados) para mostrar en el perfil."""
    unlocked_ids = set(
        UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    )
    unlocked, locked = [], []
    for badge in Badge.objects.all():
        (unlocked if badge.pk in unlocked_ids else locked).append(badge)
    return unlocked, locked
