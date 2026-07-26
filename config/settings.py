"""Configuración de Django para StarStudy.

Configuración principal del proyecto: bases de datos (SQLite con timeout),
cache (LocMemCache - solo desarrollo), autenticación por email+rol,
zona horaria Argentina, seguridad (HSTS, XSS, CSRF, X-Frame-Options),
y apps instaladas.

Para producción:
- Cambiar CACHES a Redis/Memcached
- Configurar SECRET_KEY, DEBUG=False, ALLOWED_HOSTS
- Habilitar SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE
- Configurar SECURE_HSTS_SECONDS >= 31536000 (1 año)
"""
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY no configurada. Definí SECRET_KEY en .env o variables de entorno.')

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.tasks',
    'apps.habits',
    'apps.schedule',
    'apps.courses',
    'apps.gamification',
]

# Seguridad - Valores por defecto seguros para producción
# En desarrollo (.env): DEBUG=True, SECURE_SSL_REDIRECT=False, etc.
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True') == 'True'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'True') == 'True'
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True' if not DEBUG else 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True' if not DEBUG else 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True' if not DEBUG else 'False') == 'True'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Fernet key para encriptar tokens GitHub (persistente, no rotar con SECRET_KEY)
# Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY = os.getenv('FERNET_KEY')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'apps' / 'accounts' / 'templates',
            BASE_DIR / 'apps' / 'tasks' / 'templates',
            BASE_DIR / 'apps' / 'habits' / 'templates',
            BASE_DIR / 'apps' / 'schedule' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.accounts.context_processors.user_courses',
                'apps.accounts.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {}
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        },
    }

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = ['apps.accounts.backends.EmailRoleBackend']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'es')
TIME_ZONE = os.getenv('TIME_ZONE', 'America/Argentina/Buenos_Aires')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Cache - LocMemCache solo para desarrollo (no funciona en multi-proceso)
# En producción usar Redis: 'BACKEND': 'django.core.cache.backends.redis.RedisCache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'starstudy-cache',
    }
}
