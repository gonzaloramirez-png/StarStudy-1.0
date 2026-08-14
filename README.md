<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/HTML-5-E34F26?style=flat-square&logo=html5&logoColor=white" alt="HTML">
  <img src="https://img.shields.io/badge/CSS-3-1572B6?style=flat-square&logo=css3&logoColor=white" alt="CSS">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/SQL-4479A1?style=flat-square&logo=postgresql&logoColor=white" alt="SQL">
</p>

<h1 align="center">StarStudy</h1>

<p align="center">
  Plataforma educativa inteligente con roles, gamificación y gestión de hábitos.<br>
  Diseñada para conectar <strong>estudiantes</strong>, <strong>profesores</strong>, <strong>personal</strong> y <strong>programadores</strong> en un solo entorno.
</p>

<p align="center">
  <a href="#demo">Demo</a> &bull;
  <a href="#instalación">Instalación</a> &bull;
  <a href="#docker">Docker</a> &bull;
  <a href="#características">Características</a> &bull;
  <a href="#estructura-del-proyecto">Estructura</a> &bull;
  <a href="#roles-y-permisos">Roles</a> &bull;
  <a href="#contribuir">Contribuir</a>
</p>

---

## Demo

<!-- Agregar enlace a demo desplegada -->
<!-- [![Demo](https://img.shields.io/badge/Demo-Online-brightgreen?style=for-the-badge)](https://tu-demo.vercel.app) -->

<!-- Agregar capturas de pantalla aquí -->
<!-- ![Home](screenshots/home.png) -->
<!-- ![Tasks](screenshots/tasks.png) -->
<!-- ![Gamification](screenshots/gamification.png) -->

---

## Características

<table>
  <tr>
    <td width="50%">

### Tareas
- Creación, asignación y seguimiento con niveles de importancia (Baja a Critica)
- Estados: Pendiente → En Revisión → Corregida / Devuelta
- Comentarios y snippets de corrección reutilizables
- Archivos adjuntos y exportación de calificaciones
- Vista "Mi Día" con tareas del día

    </td>
    <td width="50%">

### Gamificación
- Sistema de XP y niveles (25 XP = 1 nivel)
- Badges por logros (Académicos, Sociales, Constancia, Especiales)
- Tienda de recompensas canjeables con XP
- Quizzes auto-calificados con tiempo límite
- Rankings semanales y mensuales por curso

    </td>
  </tr>
  <tr>
    <td>

### Hábitos
- Sistema "Misión Principal" con niveles de dificultad
- Categorías con código de color: Enfoque, Esencial, Urgente, Bienestar
- Ventanas de tiempo con recordatorios automáticos
- Tracking diario de completado con analytics

    </td>
    <td>

### Horarios
- Horario personal y de curso
- Semáforo de riesgo por estudiante (Verde / Amarillo / Rojo)
- Sistema de tutorías: slots disponibles + reservas de estudiantes
- Recordatorios automáticos de schedule

    </td>
  </tr>
  <tr>
    <td>

### Cursos
- Gestión completa con códigos de invitación dinámicos
- Clonación de cursos para nuevo año académico
- Archivo/Restauración con cierre automático de códigos
- Roles de profesor titular y asistente

    </td>
    <td>

### Notificaciones
- Alertas automáticas al crear, asignar y completar tareas
- Sistema leído/no leído con contador cacheado
- Preferencias por usuario: email, in-app, push
- Digest diario vía management command

    </td>
  </tr>
  <tr>
    <td>

### Developer Workspace
- Perfil técnico con handle de GitHub y stack preferido
- Code Challenges por dificultad (Easy/Medium/Hard)
- Snippets de código con tags de lenguaje
- Architecture Decision Records (ADRs)
- Monitoreo de salud de servidores

    </td>
    <td>

### Producción
- Docker multi-stage build (Python 3.11-slim)
- Nginx con SSL, rate limiting y proxy inverso
- Celery worker + Beat para tareas asíncronas
- Sentry para monitoreo de errores
- Prometheus para métricas
- Health checks (DB, Cache, Celery, Redis, Disk, Memory)

    </td>
  </tr>
</table>

---

## Tecnologías

| Capa | Tecnología | Uso |
|------|-----------|-----|
| **Backend** | Django 6.0.6 | Framework principal |
| **Frontend** | Bootstrap 5.3 + Bootstrap Icons | UI responsive |
| **Base de datos (dev)** | SQLite | Desarrollo local |
| **Base de datos (prod)** | PostgreSQL 16 | Producción |
| **Cache (dev)** | Django LocMemCache | Cache en memoria |
| **Cache (prod)** | Redis 7 | Cache distribuido |
| **Cola de tareas** | Celery + Redis | Tareas asíncronas |
| **Scheduler** | APScheduler (dev) / Celery Beat (prod) | Tareas programadas |
| **Reverse Proxy** | Nginx | SSL, rate limiting, proxy |
| **WSGI** | Gunicorn | Servidor de producción |
| **Monitoreo** | Sentry + Prometheus | Errores y métricas |
| **Containerización** | Docker + Docker Compose | Despliegue |
| **CI/CD** | GitHub Actions | Lint, test, build, deploy |
| **Testing** | pytest + pytest-cov | Tests unitarios y coverage |
| **Linting** | Ruff | Análisis de código |

---

## Instalación

### Requisitos

- Python 3.12+
- Git
- (Opcional) PostgreSQL 16+ para producción
- (Opcional) Docker y Docker Compose para despliegue completo

### Opción rápida (recomendada)

```powershell
# 1. Clonar el repositorio
git clone https://github.com/gonzaloramirez-png/StarStudy-1.0.git
cd StarStudy-1.0

# 2. Activar entorno virtual
.\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar (aplica migraciones y abre el navegador)
python run.py
```

### Instalación paso a paso

**Windows (PowerShell):**

```powershell
git clone https://github.com/gonzaloramirez-png/StarStudy-1.0.git
cd StarStudy-1.0
.\venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Linux / macOS:**

```bash
git clone https://github.com/gonzaloramirez-png/StarStudy-1.0.git
cd StarStudy-1.0
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

### Qué hace `python run.py`

1. Aplica migraciones de base de datos automáticamente
2. Inicia el programador de tareas (recordatorios, hábitos)
3. Abre el navegador en `http://127.0.0.1:8000`
4. Inicia el servidor de desarrollo Django

### Variables de entorno

Crear archivo `.env` en la raíz del proyecto (ver `.env.example`):

```env
# Requerido
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Opcional (producción)
DATABASE_URL=postgres://user:pass@localhost:5432/starstudy
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
SENTRY_DSN=https://your-sentry-dsn
FERNET_KEY=tu-fernet-key

# Zona horaria
TIME_ZONE=America/Argentina/Buenos_Aires
```

### Crear superusuario

```powershell
python manage.py createsuperuser
```

### Ejecutar tests

```powershell
pytest apps/ tests/ --cov=apps --cov-report=term-missing
```

### Linting

```powershell
ruff check .
```

---

## Docker

### Desarrollo con Docker

```bash
docker compose up -d --build
docker compose logs -f web
```

### Producción completa

El `docker-compose.yml` incluye 6 servicios:

| Servicio | Imagen | Descripción |
|----------|--------|-------------|
| `db` | postgres:16-alpine | Base de datos PostgreSQL |
| `redis` | redis:7-alpine | Cache + Celery broker |
| `web` | Custom (Dockerfile) | Django + Gunicorn |
| `celery` | Custom (Dockerfile) | Celery worker (4 concurrent) |
| `celery-beat` | Custom (Dockerfile) | Celery Beat scheduler |
| `nginx` | nginx:alpine | Reverse proxy (puertos 80/443) |

```bash
# Desplegar todo
docker compose -f docker-compose.yml --env-file .env up -d --build

# Ver logs
docker compose logs -f web

# Parar servicios
docker compose down

# Con volúmenes persistentes
docker compose up -d -V
```

### Estructura del Dockerfile

- **Stage 1 (Builder)**: Python 3.11-slim, instala dependencias de compilación, pip install, collectstatic
- **Stage 2 (Runtime)**: Python 3.11-slim, solo dependencias de ejecución, usuario no-root (`appuser`), healthcheck

### Nginx

- SSL/TLS con Let's Encrypt o certificados auto-firmados
- Rate limiting: 10 req/s API, 5 req/min login/registro
- Archivos estáticos con cache de 1 año (WhiteNoise pre-compressed)
- Headers de seguridad (HSTS, X-Frame-Options, CSP)
- Redirect HTTP → HTTPS

---

## Primeros pasos

1. **Registrate** con el rol que necesites
2. **Si sos Profesor**: creá tareas y compartí tu código de vinculación (visible en tu perfil)
3. **Si sos Estudiante**: vinculate con el código de un profesor desde tu perfil
4. **Si sos Personal**: probá la sección "Misión Principal" (hábitos)
5. **Si sos Programador**: conectá tu cuenta de GitHub y explorá el Developer Workspace

### Roles disponibles

| Rol | Descripción |
|-----|-------------|
| **Estudiante** | Recibe tareas, completa misiones, gana XP, se vincula a profesores |
| **Profesor** | Crea y corrige tareas, gestiona cursos y horarios, da tips de XP |
| **Personal** | Gestiona hábitos, tareas personales y horarios |
| **Programador** | Developer workspace, code challenges, snippets, monitoreo |

---

## Estructura del proyecto

```
StarStudy-1.0/
├── config/                          # Configuración Django
│   ├── settings.py                  # Configuración principal (dev)
│   ├── settings_prod.py             # Configuración producción
│   ├── urls.py                      # URLs raíz
│   ├── celery.py                    # Instancia Celery
│   ├── wsgi.py / asgi.py           # Puntos de entrada
│   └── db_backends/                 # Backend MariaDB personalizado
│
├── apps/
│   ├── accounts/                    # Usuarios, autenticación, notificaciones
│   │   ├── models.py               # User, Notification, UserActivity
│   │   ├── backends.py             # EmailRoleBackend (email+rol)
│   │   ├── signals.py              # Notificaciones automáticas
│   │   ├── services.py             # Lógica de negocio
│   │   ├── decorators.py           # Decoradores de permisos
│   │   ├── cache.py                # Sistema de caché
│   │   ├── gamification.py         # Lógica de gamificación
│   │   ├── levels.py               # Sistema de niveles
│   │   ├── views/                  # home, auth, profile, push
│   │   └── templates/              # Templates de cuentas
│   │
│   ├── tasks/                       # Sistema de tareas
│   │   ├── models.py               # Task, Comment, CommentSnippet
│   │   ├── services.py             # Lógica de negocio
│   │   ├── services_export.py      # Exportación de datos
│   │   ├── tasks.py                # Celery tasks
│   │   ├── signals.py              # Auto-notificaciones
│   │   ├── views/                  # CRUD, Mi Día, grade table, export
│   │   └── templates/              # Partials reutilizables
│   │
│   ├── habits/                      # Sistema de hábitos
│   │   ├── models.py               # Habit, HabitCompletion
│   │   ├── services.py             # Lógica de negocio
│   │   ├── views/                  # CRUD, analytics
│   │   └── templates/              # Templates de hábitos
│   │
│   ├── schedule/                    # Gestión de horarios
│   │   ├── models.py               # ScheduleEntry, RiskTrafficLight, Tutoring*
│   │   ├── services.py             # Lógica de negocio
│   │   ├── scheduler.py            # APScheduler background jobs
│   │   ├── views/                  # Horarios personales y de curso
│   │   └── templates/              # Templates de schedule
│   │
│   ├── courses/                     # Gestión de cursos
│   │   ├── models.py               # Course, CourseCode, Teacher/StudentCourse
│   │   ├── views/                  # Bulk operations
│   │   └── templates/              # Templates de cursos
│   │
│   ├── gamification/                # Sistema de gamificación
│   │   ├── models.py               # Tip, Reward, Badge, Quiz, Ranking
│   │   ├── forms.py                # Formularios de gamificación
│   │   ├── views.py                # Vistas de gamificación
│   │   ├── management/commands/    # generate_rankings
│   │   └── templates/              # Templates de gamificación
│   │
│   ├── dev/                         # Developer workspace
│   │   ├── models.py               # DevProfile, Challenge, Submission, Snippet, ADR
│   │   ├── services.py             # Lógica de negocio
│   │   ├── views/                  # Dashboard, challenges, snippets, health, api
│   │   └── templates/              # Templates de dev
│   │
│   └── core/                        # Utilidades compartidas
│       ├── views.py                # CustomHealthCheckView
│       └── templatetags/           # htmx_tags
│
├── templates/                       # Templates globales
│   ├── base.html                   # Layout base (navbar, footer, toasts)
│   ├── home.html                   # Dashboard principal
│   ├── 403.html / 404.html / 500.html
│   ├── registration/               # Login, password reset, email change
│   ├── emails/                     # Templates de email
│   ├── partials/                   # Partials reutilizables
│   └── health_check/               # Health check template
│
├── static/
│   ├── css/                        # starry-night.css, components.css
│   ├── js/                         # sw.js, notifications.js, product-tour.js
│   └── img/                        # Imágenes estáticas
│
├── docker/
│   ├── nginx.conf                  # Configuración Nginx completa
│   └── entrypoint.sh               # Entrypoint Docker
│
├── tests/                           # Tests del proyecto
│   └── conftest.py                 # Fixtures pytest
│
├── docs/                            # Documentación
│   ├── architecture.md
│   ├── api.md
│   ├── roadmap.md
│   └── database.md
│
├── manage.py                        # CLI de Django
├── run.py                           # Script de inicio rápido
├── Dockerfile                       # Build multi-stage
├── docker-compose.yml               # Stack completo de producción
├── requirements.txt                 # Dependencias
├── pyproject.toml                   # Config pytest + coverage
├── build.sh                         # Build script (Render)
├── .env.example                     # Template de variables
└── .github/workflows/ci.yml         # CI/CD pipeline
```

---

## Roles y permisos

| Funcionalidad | Estudiante | Profesor | Personal | Programador |
|---|:---:|:---:|:---:|:---:|
| Ver tareas asignadas | ✅ | ✅* | ✅* | ✅* |
| Crear tareas personales | ✅ | ✅ | ✅ | ✅ |
| Asignar tareas a otros | ❌ | ✅ | ✅ | ✅ |
| Completar tareas | ✅ | ✅ | ✅ | ✅ |
| Eliminar tareas | ❌ | ✅ | ✅ | ✅ |
| Comentar en tareas | ✅ | ✅ | ✅ | ✅ |
| Corregir tareas (scoring) | ❌ | ✅ | ❌ | ❌ |
| Horario personal | ✅ | ✅ | ✅ | ✅ |
| Horario de curso (CRUD) | ❌ | ✅ | ❌ | ❌ |
| Ver horario del curso | ✅** | ❌ | ❌ | ✅ |
| Sistema de hábitos | ❌ | ❌ | ✅ | ❌ |
| Conectar GitHub | ❌ | ❌ | ❌ | ✅ |
| Vincular con profesor | ✅ | ❌ | ❌ | ❌ |
| Crear quizzes | ❌ | ✅ | ❌ | ❌ |
| Dar tips de XP | ❌ | ✅ | ❌ | ❌ |
| Gestión de cursos | ❌ | ✅ | ❌ | ❌ |
| Code Challenges | ❌ | ❌ | ❌ | ✅ |
| Developer Workspace | ❌ | ❌ | ❌ | ✅ |

\* Profesores/Personales/Programadores ven tareas que **ellos asignaron**.
\*\* Solo si están vinculados a un profesor.

---

## Arquitectura

```
                    ┌─────────────────────────────────────────┐
                    │              Nginx (443/80)              │
                    │        SSL · Rate Limit · Proxy          │
                    └──────────────┬──────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────┐
                    │           Django + Gunicorn              │
                    │     accounts · tasks · habits · schedule │
                    │      courses · gamification · dev        │
                    └──────┬───────────┬──────────┬───────────┘
                           │           │          │
                ┌──────────▼──┐  ┌─────▼────┐  ┌──▼──────────┐
                │ PostgreSQL  │  │  Redis   │  │   Celery     │
                │    16       │  │    7     │  │  Worker +    │
                │             │  │  Cache + │  │  Beat        │
                │             │  │  Broker  │  │              │
                └─────────────┘  └──────────┘  └──────────────┘
```

---

## Optimizaciones de rendimiento

- **Caché en memoria**: Estadísticas del home, profile, notificaciones y horarios se cachean (2-30 min según frecuencia de cambio)
- **Índices de base de datos**: 11+ índices en Task, Notification, User y HabitCompletion para búsquedas rápidas
- **`select_related`**: Eliminación de problemas N+1 en todas las listas
- **Anotaciones ORM**: Hábitos usan `Exists` + `Count` para calcular `completed_today` y `total_completions` en una sola query
- **`.only()`**: Querysets que traen solo los campos necesarios en listas de tareas, notificaciones y home
- **Query optimizadas**: Agregaciones con `Count` y `Q` en vez de múltiples queries

### Arquitectura de caché

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Template   │────▶│  Cache API   │────▶│  Database   │
│  (base.html) │     │ (LocMem/Redis)│    │ (SQLite/PG) │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    Invalidación por:
                    - Crear/completar tarea
                    - Leer notificación
                    - Modificar horario
```

| Dato | Timeout | Se invalida cuando... |
|---|---|---|
| Notificaciones no leídas | 2 min | Leés una notificación |
| Stats del home | 5 min | Creás/completás/eliminás una tarea |
| Stats del profile | 5 min | Creás/completás/eliminás una tarea |
| Horario del curso | 30 min | El profesor modifica el horario |

---

## CI/CD

El pipeline de GitHub Actions se ejecuta en push/PR a `main` y `develop`:

### Jobs

| Job | Descripción |
|-----|-------------|
| **Lint** | `ruff check .` para análisis de código |
| **Test** | pytest con PostgreSQL 16 como service container |
| **Build** | Docker multi-stage build → GitHub Container Registry (ghcr.io) |
| **Deploy** | Deploy a staging (placeholder) |

### Ejecución local

```powershell
# Lint
ruff check .

# Tests con coverage
pytest apps/ tests/ --cov=apps --cov-report=term-missing

# Tests específicos
pytest apps/accounts/tests.py -v
```

---

## URLs principales

| URL | Método | Descripción |
|---|---|---|
| `/` | GET | Dashboard principal |
| `/login/` | GET/POST | Iniciar sesión |
| `/register/` | GET/POST | Registrarse |
| `/profile/` | GET/POST | Ver perfil / Vincular profesor |
| `/tasks/` | GET | Lista de tareas |
| `/tasks/personal/` | GET | Tareas personales |
| `/tasks/create/` | GET/POST | Crear tarea |
| `/tasks/<id>/` | GET | Detalle de tarea |
| `/tasks/<id>/complete/` | POST | Marcar tarea completada |
| `/tasks/<id>/delete/` | POST | Eliminar tarea |
| `/tasks/my-day/` | GET | Vista "Mi Día" |
| `/tasks/grades/` | GET | Tabla de calificaciones |
| `/schedule/` | GET/POST | Horario personal |
| `/schedule/course/` | GET/POST | Horario de curso |
| `/habits/` | GET | Lista de hábitos |
| `/habits/create/` | GET/POST | Crear hábito |
| `/habits/analytics/` | GET | Analytics de hábitos |
| `/courses/` | GET | Lista de cursos |
| `/gamification/rankings/` | GET | Rankings |
| `/gamification/badges/` | GET | Badges |
| `/gamification/quizzes/` | GET | Quizzes |
| `/notifications/` | GET | Notificaciones |
| `/health/` | GET | Health check |
| `/dev/` | GET | Developer workspace |

---

## Contribuir

1. Hacé fork del repositorio
2. Creá una branch para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Hacé commit de tus cambios (`git commit -m 'feat: agregar nueva funcionalidad'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abrí un Pull Request

### Convenciones de código

- Seguir **PEP 8** para Python
- Usar **Ruff** como linter (`ruff check .`)
- Usar **conventional commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Crear `services.py` para lógica de negocio (no meter lógica en views)
- Crear `signals.py` para automatizaciones
- Usar los decoradores de `decorators.py` en vez de checks inline
- Tests con pytest para cada nueva funcionalidad
- Templates con HTMX para interacciones dinámicas

### Estructura de una app

```
apps/nueva_app/
├── __init__.py
├── admin.py          # Configuración del admin
├── apps.py           # Config de la app
├── models.py         # Modelos
├── forms.py          # Formularios
├── services.py       # Lógica de negocio
├── signals.py        # Señales Django
├── urls.py           # Rutas
├── views/            # Vistas
├── templates/        # Templates
├── tests.py          # Tests
└── migrations/       # Migraciones
```

---

## Troubleshooting

### Errores comunes

| Problema | Solución |
|----------|----------|
| `No module named 'django'` | Activar entorno virtual: `.\venv\Scripts\activate` |
| `Port 8000 already in use` | Cambiar puerto: `python run.py --port 8001` |
| `Database locked` | Cerrar otras instancias de Django |
| `Migration errors` | Eliminar `db.sqlite3` y re-ejecutar: `python run.py` |
| `Git not recognized` | Instalar Git desde https://git-scm.com |
| `Permission denied` en Docker | Verificar permisos: `chmod +x docker/entrypoint.sh` |

### Logs

```powershell
# Ver logs de Django
python manage.py runserver --verbosity=2

# Ver logs de Celery
celery -A config worker -l info

# Ver logs de Docker
docker compose logs -f web
docker compose logs -f celery
```

---

## Licencia

Uso educativo. Este proyecto fue desarrollado como parte de un proyecto académico.

---

## Equipo

Desarrollado por [gonzaloramirez-png](https://github.com/gonzaloramirez-png)

---

<p align="center">
  Hecho con ❤️ para estudiantes
</p>
