"""Scheduler APScheduler: tareas en background para notificaciones y rankings.

- check_habit_notifications: cada 1 min, verifica hábitos con hora de inicio/fin
- check_task_deadlines: cada 1 min, verifica tareas que vencen hoy
- generate_weekly_rankings: cada lunes a medianoche, genera rankings semanales
- generate_monthly_rankings: día 1 de cada mes a medianoche, genera rankings mensuales
- start: inicia el scheduler (solo una vez). Se llama desde AppConfig.ready().
- shutdown: detiene el scheduler limpiamente.
"""
import atexit
import logging
from datetime import time, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
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


def generate_weekly_rankings():
    """Genera rankings semanales para todos los cursos activos."""
    from apps.courses.models import Course
    from apps.gamification.models import Ranking

    courses = Course.objects.filter(status=Course.Status.ACTIVE)
    total = 0
    for course in courses:
        count = Ranking.generate_weekly(course)
        total += count
    logger.info(f'Rankings semanales generados: {total} estudiantes en {courses.count()} cursos')


def generate_monthly_rankings():
    """Genera rankings mensuales para todos los cursos activos."""
    from apps.courses.models import Course
    from apps.gamification.models import Ranking

    courses = Course.objects.filter(status=Course.Status.ACTIVE)
    total = 0
    for course in courses:
        count = Ranking.generate_monthly(course)
        total += count
    logger.info(f'Rankings mensuales generados: {total} estudiantes en {courses.count()} cursos')


def start():
    global _started
    if _started:
        return
    try:
        # Jobs existentes
        scheduler.add_job(check_habit_notifications, 'interval', minutes=1, id='habits', replace_existing=True)
        scheduler.add_job(check_task_deadlines, 'interval', minutes=1, id='deadlines', replace_existing=True)

        # Rankings automáticos
        # Semanal: todos los lunes a las 00:05
        scheduler.add_job(
            generate_weekly_rankings,
            CronTrigger(day_of_week='mon', hour=0, minute=5),
            id='weekly_rankings',
            replace_existing=True,
        )
        # Mensual: día 1 de cada mes a las 00:10
        scheduler.add_job(
            generate_monthly_rankings,
            CronTrigger(day=1, hour=0, minute=10),
            id='monthly_rankings',
            replace_existing=True,
        )

        scheduler.start()
        _started = True
        atexit.register(shutdown)
        logger.info('APScheduler iniciado con jobs de rankings')
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