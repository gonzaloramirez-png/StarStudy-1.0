"""Helpers centralizados para tests de StarStudy.

Este archivo centraliza funciones de utilidad usadas en tests de todas las apps.
Para usar en tests: from tests.helpers import make_user, make_task
"""
from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User


def make_user(email='test@starstudy.local', role='STUDENT', password='claveSegura123', **kwargs):
    """Crea un usuario de prueba con el email y rol especificados."""
    user = User.objects.create_user(
        email=email,
        password=password,
        role=role,
        **kwargs,
    )
    return user


def make_task(assigned_by, assigned_to=None, **kwargs):
    """Crea una tarea de prueba con valores por defecto razonables."""
    from apps.tasks.models import Task
    defaults = {
        'title': 'Tarea de prueba',
        'importance': Task.Importance.MEDIUM,
        'deadline': timezone.now() + timedelta(days=1),
        'assigned_by': assigned_by,
        'assigned_to': assigned_to or assigned_by,
    }
    defaults.update(kwargs)
    return Task.objects.create(**defaults)
