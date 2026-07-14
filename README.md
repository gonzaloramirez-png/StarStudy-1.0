<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-green?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap">
  <img src="https://img.shields.io/badge/License-Educational-yellow?style=for-the-badge" alt="License">
</p>

<h1 align="center">StarStudy</h1>

<p align="center">
  Plataforma educativa inteligente con roles, gamificación y gestión de hábitos.<br>
  Diseñada para conectar <strong>estudiantes</strong>, <strong>profesores</strong>, <strong>personal</strong> y <strong>programadores</strong> en un solo entorno.
</p>

<p align="center">
  <a href="#instalación">Instalación</a> &bull;
  <a href="#primeros-pasos">Primeros pasos</a> &bull;
  <a href="#estructura-del-proyecto">Estructura</a> &bull;
  <a href="#roles-y-permisos">Roles</a> &bull;
  <a href="#contribuir">Contribuir</a>
</p>

---

## Características

| Funcionalidad | Descripción |
|---|---|
| **Tareas** | Creación, asignación y seguimiento con niveles de importancia (Baja → Crítica). Filtros por estado, urgencia y búsqueda. |
| **Horarios** | Gestión de horarios personales y de curso. Vista de mapa interactivo para programadores. |
| **Hábitos** | Sistema "Misión Principal": completá un hábito diario para subir de nivel. |
| **Notificaciones** | Alertas automáticas al crear, asignar y completar tareas. Sistema de notificaciones leídas/no leídas. |
| **Vinculación** | Profesores generan un código. Estudiantes lo usan para vincularse automáticamente. |
| **Gamificación** | Sistema de niveles, XP y misiones. Cada tarea completada suma puntos. |
| **GitHub** | Programadores pueden conectar su cuenta de GitHub. |
| **Cache** | Sistema de caché en memoria para datos que no cambian seguido (stats, notificaciones, horarios). |

---

## Capturas

<!-- Agregar capturas de pantalla aquí -->
<!-- ![Home](screenshots/home.png) -->
<!-- ![Tasks](screenshots/tasks.png) -->
<!-- ![Schedule](screenshots/schedule.png) -->

---

## Tecnologías

| Capa | Tecnología |
|----|-----|
| Backend | Django 6.0.6 |
| Frontend | Bootstrap 5.3 + Bootstrap Icons |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción) |
| Cache | Django LocMem Cache |
| Notificaciones | APScheduler |
| Python | 3.12+ |

---

## Instalación

### Opción rápida (recomendada)

```powershell
# 1. Clonar el repositorio
git clone https://github.com/chaloramirezzuniga-png/StarStudy-1.0.git
cd StarStudy-1.0

# 2. Activar entorno virtual (ya incluido)
.\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar (aplica migraciones y abre el navegador automáticamente)
python run.py
```

### Instalación paso a paso

**Requisitos:**
- Python 3.12+ instalado
- Git instalado

**Windows (PowerShell):**
```powershell
# Clonar
git clone https://github.com/chaloramirezzuniga-png/StarStudy-1.0.git
cd StarStudy-1.0

# Activar entorno virtual
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python run.py
```

**Linux / macOS (Terminal):**
```bash
# Clonar
git clone https://github.com/chaloramirezzuniga-png/StarStudy-1.0.git
cd StarStudy-1.0

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar servidor
python3 run.py
```

### Qué hace `python run.py`
1. Aplica migraciones de base de datos automáticamente
2. Inicia el programador de tareas (recordatorios, hábitos)
3. Abre el navegador en http://127.0.0.1:8000

### Variables de entorno (opcional)

Crear archivo `.env` en la raíz:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
TIME_ZONE=America/Argentina/Buenos_Aires
```

### Crear admin (opcional)

```powershell
python manage.py createsuperuser
```

---

---

## Primeros pasos

1. **Registrate** con el rol que necesites
2. **Si sos Profesor**: creá tareas y compartí tu código de vinculación (visible en tu perfil)
3. **Si sos Estudiante**: vinculate con el código de un profesor desde tu perfil
4. **Si sos Personal**: probá la sección "Misión Principal" (hábitos)
5. **Si sos Programador**: conectá tu cuenta de GitHub y explorá la vista de mapa

---

## Estructura del proyecto

```
StarStudy-1.0/
├── config/                  # Configuración del proyecto Django
│   ├── settings.py          # Configuración principal
│   ├── urls.py              # URLs raíz
│   └── wsgi.py              # Punto de entrada WSGI
│
├── apps/
│   ├── accounts/            # Usuarios, autenticación, notificaciones
│   │   ├── models.py        # User, Notification
│   │   ├── views/           # home, auth, profile
│   │   ├── services.py      # Lógica de negocio
│   │   ├── cache.py         # Sistema de caché
│   │   ├── signals.py       # Notificaciones automáticas
│   │   ├── backends.py      # Backend de autenticación
│   │   └── decorators.py    # Decoradores de permisos
│   │
│   ├── tasks/               # Sistema de tareas
│   │   ├── models.py        # Task, Comment
│   │   ├── views/           # CRUD de tareas
│   │   ├── services.py      # Lógica de negocio
│   │   ├── filters.py       # Filtros de búsqueda
│   │   ├── signals.py       # Notificaciones automáticas
│   │   └── templates/       # Partials reutilizables (_importance_badge, _task_actions)
│   │
│   ├── habits/              # Sistema de hábitos
│   │   ├── models.py        # Habit, HabitCompletion
│   │   ├── views/           # CRUD de hábitos
│   │   ├── services.py      # Lógica de negocio
│   │   └── signals.py       # Notificaciones automáticas
│   │
│   └── schedule/            # Gestión de horarios
│       ├── models.py        # ScheduleEntry
│       ├── views/           # Horarios personales y de curso
│       ├── services.py      # Lógica de negocio
│       ├── signals.py       # Notificaciones automáticas
│       ├── scheduler.py     # Tareas programadas (APScheduler)
│       └── utils.py         # Utilidades de formato
│
├── templates/               # Templates globales
│   ├── base.html            # Layout base (navbar, footer, toasts)
│   ├── home.html            # Dashboard principal
│   ├── 404.html             # Página no encontrada
│   └── 500.html             # Error del servidor
│
├── static/
│   └── css/
│       └── starry-night.css # Estilos principales (tema Noche Estrellada)
│
├── db.sqlite3               # Base de datos (desarrollo)
├── manage.py                # CLI de Django
├── run.py                   # Script de inicio rápido
└── requirements.txt         # Dependencias
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
| Horario personal | ✅ | ✅ | ✅ | ✅ |
| Horario de curso (CRUD) | ❌ | ✅ | ❌ | ❌ |
| Ver horario del curso | ✅** | ❌ | ❌ | ✅ |
| Sistema de hábitos | ❌ | ❌ | ✅ | ❌ |
| Conectar GitHub | ❌ | ❌ | ❌ | ✅ |
| Vincular con profesor | ✅ | ❌ | ❌ | ❌ |

\* Profesores/Personales/Programadores ven tareas que **ellos asignaron**.
\*\* Solo si están vinculados a un profesor.

---

## Optimizaciones de rendimiento

- **Caché en memoria**: Estadísticas del home, profile, notificaciones y horarios se cachean (2-30 min según frecuencia de cambio)
- **Índices de base de datos**: 11 índices en Task, Notification, User y HabitCompletion para búsquedas rápidas
- **`select_related`**: Eliminación de problemas N+1 en todas las listas
- **Anotaciones ORM**: Hábitos usan `Exists` + `Count` para calcular `completed_today` y `total_completions` en una sola query (antes eran N+2 queries por hábito)
- **`.only()`**: Querysets que traen solo los campos necesarios en listas de tareas, notificaciones y home
- **Query optimizadas**: Agregaciones con `Count` y `Q` en vez de múltiples queries

---

## Arquitectura de caché

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Template   │────▶│  Cache API   │────▶│  Database   │
│  (base.html) │     │  (LocMem)   │     │  (SQLite)   │
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
| `/tasks/<id>/complete/` | POST | Marcar tarea como completada |
| `/tasks/<id>/delete/` | POST | Eliminar tarea |
| `/schedule/` | GET/POST | Horario personal |
| `/schedule/course/` | GET/POST | Horario de curso (profesor) |
| `/schedule/student/course/` | GET | Ver horario del curso (estudiante) |
| `/habitos/` | GET | Lista de hábitos |
| `/habitos/create/` | GET/POST | Crear hábito |
| `/notifications/` | GET | Lista de notificaciones |

---

## Contribuir

1. Hacé fork del repositorio
2. Creá una branch para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Hacé commit de tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abrí un Pull Request

### Convenciones de código

- Seguir PEP 8 para Python
- Usar templates tags de Django en vez de JavaScript inline
- Crear `services.py` para lógica de negocio (no meter lógica en views)
- Crear `signals.py` para automatizaciones
- Usar los decoradores de `decorators.py` en vez de checks inline

---

## Licencia

Uso educativo.

---

<p align="center">
  Hecho con ❤️ para estudiantes
</p>
