"""Tareas Celery de la app tasks.

- send_task_deadline_reminders: ejecutada por Celery Beat cada hora; envía
  un recordatorio por email a las tareas pendientes que vencen pronto.
"""
from celery import shared_task

from apps.tasks.services import send_task_reminders


@shared_task
def send_task_deadline_reminders():
    return send_task_reminders()
