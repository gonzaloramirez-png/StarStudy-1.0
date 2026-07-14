"""Sistema de cache centralizado con LocMemCache.

⚠️ ADVERTENCIA: LocMemCache NO funciona en multi-proceso (gunicorn workers > 1).
   En producción usar Redis: CACHES['default']['BACKEND'] = 'django.core.cache.backends.redis.RedisCache'

Funciones genéricas _get()/_invalidate() para evitar repetición.
Cachés: unread (2 min), home (5 min), profile (5 min), schedule (30 min).
Se debe llamar a invalidate_* después de cada escritura que afecte los datos cacheados.
"""
from django.core.cache import cache

TIMEOUTS = {'unread': 120, 'home': 300, 'profile': 300, 'schedule': 1800}


def _get(key, timeout, fetch_fn):
    """Obtiene valor del cache; si no existe, ejecuta fetch_fn y lo cachea."""
    val = cache.get(key)
    if val is None:
        val = fetch_fn()
        cache.set(key, val, timeout)
    return val


def _invalidate(key):
    """Elimina una clave del cache."""
    cache.delete(key)


def get_unread_count(user):
    """Cache: cantidad de notificaciones no leídas del usuario (2 min)."""
    return _get(f'unread_{user.pk}', TIMEOUTS['unread'],
                lambda: user.notifications.filter(is_read=False).count())


def invalidate_unread(user):
    """Invalida el cache de notificaciones no leídas."""
    _invalidate(f'unread_{user.pk}')


def get_home_stats(user_id, fetch_fn):
    """Cache: estadísticas del home (pendientes, vencidas, recientes) (5 min)."""
    return _get(f'home_{user_id}', TIMEOUTS['home'], fetch_fn)


def invalidate_home(user_id):
    """Invalida el cache del home."""
    _invalidate(f'home_{user_id}')


def get_profile_stats(user_id, fetch_fn):
    """Cache: estadísticas del perfil (asignadas, completadas, pendientes) (5 min)."""
    return _get(f'profile_{user_id}', TIMEOUTS['profile'], fetch_fn)


def invalidate_profile(user_id):
    """Invalida el cache del perfil."""
    _invalidate(f'profile_{user_id}')


def get_course_schedule(teacher_id, fetch_fn):
    """Cache: horario del curso del profesor (30 min)."""
    return _get(f'schedule_{teacher_id}', TIMEOUTS['schedule'], fetch_fn)


def invalidate_course_schedule(teacher_id):
    """Invalida el cache del horario del curso."""
    _invalidate(f'schedule_{teacher_id}')