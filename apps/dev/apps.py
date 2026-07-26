"""App config para dev workspace."""
from django.apps import AppConfig


class DevConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dev'
    verbose_name = 'DEV Workspace'
