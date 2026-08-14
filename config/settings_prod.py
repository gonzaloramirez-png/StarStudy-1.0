"""Configuración de producción para StarStudy.

Hereda de settings.py y sobrescribe valores para entorno productivo.
Se activa con: DJANGO_SETTINGS_MODULE=config.settings_prod
"""
from .settings import *  # noqa: F403,F401
import dj_database_url
import os
import sentry_sdk
from celery.schedules import crontab
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# ----------------------------------------
# Seguridad obligatoria en producción
# ----------------------------------------
DEBUG = False

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY es obligatoria en producción.')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError('ALLOWED_HOSTS es obligatoria en producción.')

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
if CSRF_TRUSTED_ORIGINS == ['']:
    CSRF_TRUSTED_ORIGINS = []

# ----------------------------------------
# Base de datos
# ----------------------------------------
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'starstudy'),
            'USER': os.getenv('DB_USER', 'starstudy'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'db'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
            'CONN_HEALTH_CHECKS': True,
        }
    }

# ----------------------------------------
# Cache: Redis
# ----------------------------------------
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'starstudy',
    }
}

# ----------------------------------------
# Celery
# ----------------------------------------
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_ACKS_LATE = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Horarios por defecto de Celery Beat (editables desde el admin de django_celery_beat)
CELERY_BEAT_SCHEDULE = {
    'task-deadline-reminders': {
        'task': 'apps.tasks.tasks.send_task_deadline_reminders',
        'schedule': crontab(minute='0'),
    },
}

# ----------------------------------------
# Email real (SMTP)
# ----------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'StarStudy <noreply@starstudy.local>')

if not all([EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD]):
    raise ValueError('EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD son obligatorios en producción.')

# ----------------------------------------
# Static files: Manifest + compresión
# ----------------------------------------
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
WHITENOISE_USE_FINDERS = False
WHITENOISE_MANIFEST_STRICT = False

# ----------------------------------------
# Apps de observabilidad
# ----------------------------------------
INSTALLED_APPS += [
    'health_check',
    'health_check.contrib.celery',
    'health_check.contrib.redis',
    'django_prometheus',
    'django_celery_beat',
]

# ----------------------------------------
# Sentry
# ----------------------------------------
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR,
    )
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(transaction_style='url'),
            RedisIntegration(),
            CeleryIntegration(),
            sentry_logging,
        ],
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        send_default_pii=True,
        environment=os.getenv('SENTRY_ENVIRONMENT', 'production'),
        release=os.getenv('APP_VERSION', 'unknown'),
    )

# ----------------------------------------
# Logging estructurado (JSON + trace IDs)
# ----------------------------------------
import logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'fmt': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
        'console': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'level': 'INFO', 'handlers': ['console'], 'propagate': False},
        'django.request': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
        'django.security': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
        'django.db.backends': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
        'apps': {'level': 'INFO', 'handlers': ['console'], 'propagate': False},
        'celery': {'level': 'INFO', 'handlers': ['console'], 'propagate': False},
        'sentry_sdk': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
    },
}

# ----------------------------------------
# Health Check configuración
# ----------------------------------------
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # % disco
    'MEMORY_MIN': 100,     # MB RAM libre
    'CHECKS': [
        'health_check.checks.Cache',
        'health_check.checks.Database',
        'health_check.checks.DNS',
        'health_check.checks.Storage',
        'health_check.contrib.celery.CeleryPingCheck',
        'health_check.contrib.redis.RedisCheck',
    ],
}

# ----------------------------------------
# Prometheus métricas
# ----------------------------------------
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
] + MIDDLEWARE + [
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# ----------------------------------------
# Seguridad extra
# ----------------------------------------
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ----------------------------------------
# Content Security Policy (básico)
# ----------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'