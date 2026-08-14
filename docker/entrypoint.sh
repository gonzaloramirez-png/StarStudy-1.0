#!/bin/bash
# ========================================
# StarStudy - Entrypoint Docker
# ========================================
# Ejecuta migraciones, collectstatic y arranca gunicorn/celery
# ========================================

set -e  # Falla rápido si algo falla

echo "=== StarStudy Entrypoint ==="
echo "Comando: $@"

# Función para esperar a que la DB esté lista
wait_for_db() {
    echo "Esperando a PostgreSQL en ${DB_HOST:-db}:${DB_PORT:-5432}..."
    until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-starstudy}" -d "${DB_NAME:-starstudy}" > /dev/null 2>&1; do
        sleep 1
    done
    echo "PostgreSQL listo."
}

# Función para esperar a Redis
wait_for_redis() {
    echo "Esperando a Redis en ${REDIS_HOST:-redis}:${REDIS_PORT:-6379}..."
    until redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; do
        sleep 1
    done
    echo "Redis listo."
}

# Esperar dependencias según el servicio
case "$1" in
    web|celery|celery-beat)
        wait_for_db
        wait_for_redis
        ;;
esac

# Migraciones (idempotente)
if [ "$1" = "web" ] || [ "$1" = "celery" ] || [ "$1" = "celery-beat" ] || [ "$1" = "migrate" ]; then
    echo "Aplicando migraciones..."
    python manage.py migrate --noinput
fi

# Collectstatic (solo web, idempotente)
if [ "$1" = "web" ]; then
    echo "Recopilando estáticos..."
    python manage.py collectstatic --noinput --clear
fi

# Crear superusuario si no existe (opcional, para primer deploy)
if [ "$1" = "web" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Verificando/creando superusuario..."
    python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || true
fi

# Ejecutar comando principal
echo "Iniciando: $@"
exec "$@"