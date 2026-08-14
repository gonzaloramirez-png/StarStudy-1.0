# ========================================
# StarStudy - Dockerfile multi-stage
# ========================================
# Stage 1: Builder - instala dependencias y compila estáticos
# Stage 2: Runtime - imagen ligera solo con lo necesario
# ========================================

# ---------- STAGE 1: BUILDER ----------
FROM python:3.11-slim AS builder

# Evita prompts interactivos y cache de pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias de sistema para compilar (pymysql, pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia solo requirements para aprovechar cache de capas
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# Copia código y compila estáticos
COPY . .
RUN mkdir -p staticfiles && python manage.py collectstatic --noinput --clear

# ---------- STAGE 2: RUNTIME ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings_prod

# Usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Dependencias runtime mínimas (libpq para PostgreSQL, libjpeg para Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia dependencias instaladas del builder
COPY --from=builder /install /usr/local
# Copia código y estáticos compilados
COPY --from=builder /app /app

# Permisos
RUN chown -R appuser:appuser /app
USER appuser

# Puerto expuesto (gunicorn)
EXPOSE 8000

# Healthcheck para Docker/Orchestrator
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Entrypoint ejecuta migraciones, collectstatic (idempotente) y gunicorn
ENTRYPOINT ["/app/docker/entrypoint.sh"]