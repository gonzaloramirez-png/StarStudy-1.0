"""Scheduler APScheduler: tareas en background para notificaciones.

- check_habit_notifications: cada 1 min, verifica hábitos con hora de inicio/fin
  dentro de ventana de ±2 min. Crea notificación si no fue enviada hoy.
- check_task_deadlines: cada 1 min, verifica tareas no personales que vencen hoy
  (deadline en últimos 2 min). Notifica al creador de la tarea.
- start: inicia el scheduler (solo una vez). Se llama desde AppConfig.ready().
- shutdown: detiene el scheduler limpiamente.
"""
import atexit
import logging
from datetime import time, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
_started = False


def _time_in_window(target: time, now_dt: timezone.datetime, window_minutes: int = 2) -> bool:
    """Verifica si una time está dentro de ±window_minutes de now_dt, manejando medianoche."""
    now_time = now_dt.time()
    window = timedelta(minutes=window_minutes)
    start = (timezone.datetime.combine(timezone.datetime.today(), now_time) - window).time()
    end = (timezone.datetime.combine(timezone.datetime.today(), now_time) + window).time()
    if start <= end:
        return start <= target <= end
    return target >= start or target <= end


def check_habit_notifications():
    from apps.habits.models import Habit
    from apps.accounts.models import Notification
    from apps.accounts.cache import invalidate_unread

    now_dt = timezone.now()
    today = now_dt.date()

    # Solo hábitos con horarios definidos (no 00:00) de usuarios activos
    habits = Habit.objects.select_related('user').exclude(
        start_time=time(0, 0), end_time=time(0, 0)
    ).filter(user__is_active=True)

    for habit in habits:
        for time_field, tipo in [(habit.start_time, 'inicio'), (habit.end_time, 'fin')]:
            if _time_in_window(time_field, now_dt, 2):
                notif_key = f"habit_{tipo}_{habit.pk}_{today}"
                already_sent = Notification.objects.filter(
                    user=habit.user,
                    meta_key=notif_key,
                ).exists()
                if not already_sent:
                    msg_map = {
                        'inicio': f'¡Hora de comenzar "{habit.title}"!',
                        'fin': f'¡Hora de terminar "{habit.title}"!',
                    }
                    with transaction.atomic():
                        Notification.objects.create(
                            user=habit.user,
                            message=msg_map[tipo],
                            link='/habitos/',
                            meta_key=notif_key,
                        )
                    invalidate_unread(habit.user)


def check_task_deadlines():
    from apps.tasks.models import Task
    from apps.accounts.models import Notification
    from apps.accounts.cache import invalidate_unread

    now_dt = timezone.now()
    two_min_ago = now_dt - timedelta(minutes=2)

    expiring = Task.objects.filter(
        is_completed=False,
        deadline__gte=two_min_ago,
        deadline__lte=now_dt,
        is_personal=False,
    ).select_related('assigned_by', 'assigned_to')

    for task in expiring:
        notif_key = f"deadline_{task.pk}_{task.deadline.date()}"
        already_sent = Notification.objects.filter(
            user=task.assigned_by,
            meta_key=notif_key,
        ).exists()
        if not already_sent:
            with transaction.atomic():
                Notification.objects.create(
                    user=task.assigned_by,
                    message=f'Vence hoy: "{task.title}" de {task.assigned_to.get_full_name() or task.assigned_to.email}',
                    link=f'/tasks/{task.pk}/',
                    meta_key=notif_key,
                )
            invalidate_unread(task.assigned_by)


def start():
    global _started
    if _started:
        return
    try:
        scheduler.add_job(check_habit_notifications, 'interval', minutes=1, id='habits', replace_existing=True)
        scheduler.add_job(check_task_deadlines, 'interval', minutes=1, id='deadlines', replace_existing=True)
        scheduler.start()
        _started = True
        atexit.register(shutdown)
        logger.info('APScheduler iniciado')
    except Exception as e:
        logger.exception('Error al iniciar el scheduler: %s', e)


def shutdown():
    global _started
    if _started:
        try:
            scheduler.shutdown(wait=False)
            _started = False
            logger.info('APScheduler detenido')
        except Exception as e:
            logger.exception('Error al detener el scheduler: %s', e)