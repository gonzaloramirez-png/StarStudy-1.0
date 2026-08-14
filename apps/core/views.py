from health_check.views import HealthCheckView


class CustomHealthCheckView(HealthCheckView):
    """Health check view con solo checks esenciales (Cache + Database)."""
    
    checks = (
        'health_check.cache.backends.Cache',
        'health_check.db.backends.DatabaseBackend',
    )