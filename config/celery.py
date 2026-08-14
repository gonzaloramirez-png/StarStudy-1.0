"""Configuración de Celery para StarStudy.

Define la instancia de la aplicación Celery usada por los servicios
`celery` y `celery-beat` del docker-compose.

Uso:
    celery -A config worker --loglevel=info
    celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
"""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
