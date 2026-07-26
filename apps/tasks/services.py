"""Servicios de tasks: lógica de negocio para CRUD de tareas y comentarios.

Funciones:
- get_task_queryset: retorna queryset optimizado según rol (creador vs receptor).
- apply_filters: aplica filtros de importancia y estado (pendiente/completada/vencida).
- create_task: crea tarea y invalida caches de ambos usuarios.
- complete_task: marca tarea completada, notifica al creador.
- delete_task: elimina tarea, captura datos antes de borrar, invalida caches.
- add_comment: crea comentario en una tarea.
"""
from django.utils import timezone
from apps.tasks.models import Task, Comment
from apps.accounts.models import Notification
from apps.accounts.cache import invalidate_home, invalidate_profile, invalidate_unread


LIST_FIELDS = ['id', 'title', 'importance', 'deadline', 'is_completed', 'is_personal', 'assigned_to_id', 'assigned_by_id']

def get_task_queryset(user, is_personal=False):
    if user.role in ('TEACHER', 'STAFF', 'PROGRAMMER'):
        return Task.objects.filter(
            assigned_by=user,
            is_personal=is_personal,
        ).select_related('assigned_to', 'assigned_by').only(*LIST_FIELDS)
    return Task.objects.filter(
        assigned_to=user,
        is_personal=is_personal,
    ).select_related('assigned_to', 'assigned_by').only(*LIST_FIELDS)


def apply_filters(queryset, importance=None, status=None, now=None):
    if importance:
        queryset = queryset.filter(importance=importance)
    if status == 'pending':
        queryset = queryset.filter(is_completed=False)
    elif status == 'completed':
        queryset = queryset.filter(is_completed=True)
    elif status == 'overdue' and now:
        queryset = queryset.filter(is_completed=False, deadline__lt=now)
    return queryset


def _invalidate_task_caches(user):
    invalidate_home(user.pk)
    invalidate_profile(user.pk)


def create_task(form, user, is_personal=False):
    task = form.save(commit=False)
    task.assigned_by = user
    if is_personal:
        task.is_personal = True
        task.assigned_to = user
    task.save()
    _invalidate_task_caches(user)
    if task.assigned_to != user:
        _invalidate_task_caches(task.assigned_to)
    return task


def complete_task(task, user):
    task.is_completed = True
    task.completed_at = timezone.now()
    task.save()

    _invalidate_task_caches(user)
    if task.assigned_by != user:
        _invalidate_task_caches(task.assigned_by)

    if not task.is_personal:
        Notification.objects.create(
            user=task.assigned_by,
            message=f'{user.get_full_name() or user.email} completó: {task.title}',
            link=f'/tasks/{task.pk}/',
        )
        invalidate_unread(task.assigned_by)

    # Registrar actividad para streaks
    from apps.accounts.models import UserActivity
    UserActivity.record_activity(user, 'task')

    return task


def delete_task(task):
    personal = task.is_personal
    assigned_by = task.assigned_by
    assigned_to = task.assigned_to
    task.delete()
    _invalidate_task_caches(assigned_by)
    if assigned_to != assigned_by:
        _invalidate_task_caches(assigned_to)
    return personal, task.pk


def add_comment(task, user, text):
    return Comment.objects.create(
        task=task,
        user=user,
        text=text,
    )
