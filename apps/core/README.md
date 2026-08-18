# App: Core

Funcionalidad compartida: health checks y template tags HTMX.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `views.py` | CustomHealthCheckView (Cache + Database) |
| `templatetags/` | Template tags personalizados para HTMX |

## Componentes

- **CustomHealthCheckView**: Health check endpoint que verifica Cache y Database
- **HTMX Tags**: Tags personalizados para templates HTMX (`hx_tags.py`)
