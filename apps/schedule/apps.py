"""Configuración de la app schedule: inicia APScheduler al arrancar el servidor."""
import sys
import atexit
from django.apps import AppConfig


class ScheduleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.schedule'
    label = 'schedule'

    def ready(self):
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0] if sys.argv else False:
            from .scheduler import start, shutdown
            start()
            atexit.register(shutdown)
