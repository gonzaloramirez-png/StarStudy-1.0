"""Servicios de accounts: lógica de negocio para perfil, vinculación, GitHub y notificaciones.

Funciones:
- get_user_stats: estadísticas del perfil con cache.
- link_student_to_teacher: vincula estudiante a profesor por código.
- connect_github / disconnect_github: gestiona cuenta GitHub (solo programadores).
- mark_notification_read: marca notificación leída e invalida cache.
- email_change_token / confirm_email_change: cambio de correo con confirmación.
- soft_delete_account: baja lógica de la cuenta (GDPR).
- export_user_data: exportación de datos personales (GDPR).
"""
import datetime

from django.core import signing
from django.db.models import Count, Q
from apps.accounts.models import User, Notification, NotificationPreferences
from apps.accounts.cache import (
    get_profile_stats, invalidate_profile,
    invalidate_unread, invalidate_home,
)

EMAIL_CHANGE_SALT = 'email-change'
EMAIL_CHANGE_MAX_AGE = 86400  # 24 horas


def get_user_stats(user):
    from apps.tasks.models import Task

    can_assign = user.role in ('TEACHER', 'STAFF', 'PROGRAMMER')

    def fetch():
        task_stats = Task.objects.filter(
            Q(assigned_by=user) | Q(assigned_to=user)
        ).aggregate(
            assigned=Count('id', filter=Q(assigned_by=user, is_personal=False)),
            completed=Count('id', filter=Q(assigned_to=user, is_completed=True)),
            pending=Count('id', filter=Q(assigned_to=user, is_completed=False)),
        )
        students = list(user.linked_students.all()) if can_assign else []
        return {
            'assigned': task_stats['assigned'],
            'completed': task_stats['completed'],
            'pending': task_stats['pending'],
            'students': students,
        }

    return get_profile_stats(user.pk, fetch)


def link_student_to_teacher(user, code):
    code = code.strip().upper()
    teacher = User.objects.filter(code=code).exclude(role=User.Role.STUDENT).first()
    if teacher:
        user.linked_to = teacher
        user.save(update_fields=['linked_to'])
        return True, teacher
    return False, None


def connect_github(user, username, token=None):
    username = username.strip()
    if not username:
        return False
    user.github_username = username
    if token:
        user.set_github_token(token)
    user.save(update_fields=['github_username', 'github_token'])
    return True


def disconnect_github(user):
    user.github_username = None
    user.github_token = None
    user.save(update_fields=['github_username', 'github_token'])


def mark_notification_read(notification):
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    invalidate_unread(notification.user)
    return notification


def email_change_token(user):
    return signing.dumps(
        {'uid': user.pk, 'email': user.pending_email},
        salt=EMAIL_CHANGE_SALT,
    )


def confirm_email_change(user, token):
    try:
        data = signing.loads(token, salt=EMAIL_CHANGE_SALT, max_age=EMAIL_CHANGE_MAX_AGE)
    except signing.BadSignature:
        return False
    if data.get('uid') != user.pk or data.get('email') != user.pending_email:
        return False
    user.email = user.pending_email
    user.pending_email = None
    user.save(update_fields=['email', 'pending_email'])
    invalidate_profile(user.pk)
    return True


def soft_delete_account(user):
    user.is_active = False
    user.email = f'deleted_{user.pk}@invalido.local'
    user.username = f'deleted_{user.pk}'
    user.first_name = ''
    user.last_name = ''
    user.github_username = None
    user.github_token = None
    user.avatar = None
    user.pending_email = None
    user.code = None
    user.linked_to = None
    user.save(update_fields=[
        'is_active', 'email', 'username', 'first_name', 'last_name',
        'github_username', 'github_token', 'avatar', 'pending_email',
        'code', 'linked_to',
    ])
    invalidate_profile(user.pk)
    invalidate_unread(user)


def _jsonable(value):
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    return value


def export_user_data(user):
    from apps.tasks.models import Task, Comment
    from apps.habits.models import Habit, HabitCompletion
    from apps.schedule.models import ScheduleEntry

    def rows(qs, fields):
        return [{f: _jsonable(r[f]) for f in fields} for r in qs.values(*fields)]

    prefs, _ = NotificationPreferences.objects.get_or_create(user=user)
    return {
        'exportado_en': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'perfil': {
            'email': user.email,
            'rol': user.role,
            'nombre': user.get_full_name(),
            'fecha_registro': _jsonable(user.date_joined),
            'vinculado_a': user.linked_to.email if user.linked_to else None,
            'github': user.github_username,
            'preferencias_notificacion': {
                'email_deadlines': prefs.email_deadlines,
                'in_app': prefs.in_app,
                'push': prefs.push,
            },
        },
        'tareas': rows(
            Task.objects.filter(Q(assigned_by=user) | Q(assigned_to=user)),
            ['id', 'title', 'description', 'importance', 'deadline',
             'is_completed', 'completed_at', 'is_personal', 'created_at',
             'assigned_by__email', 'assigned_to__email'],
        ),
        'comentarios': rows(
            Comment.objects.filter(user=user),
            ['id', 'task__title', 'text', 'created_at'],
        ),
        'habitos': rows(
            Habit.objects.filter(user=user),
            ['id', 'title', 'start_time', 'end_time', 'level', 'created_at'],
        ),
        'completaciones_habitos': rows(
            HabitCompletion.objects.filter(habit__user=user),
            ['id', 'habit__title', 'date', 'completed_at'],
        ),
        'horarios': rows(
            ScheduleEntry.objects.filter(user=user),
            ['id', 'day', 'start_time', 'end_time', 'title', 'entry_type', 'schedule_type'],
        ),
        'notificaciones': rows(
            Notification.objects.filter(user=user),
            ['id', 'message', 'link', 'is_read', 'created_at'],
        ),
        'badges': user.badges,
    }
