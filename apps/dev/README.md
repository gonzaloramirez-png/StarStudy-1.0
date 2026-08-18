# App: Dev

Developer Workspace: dashboard técnico, challenges, snippets, ADRs, health checks y API.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `models.py` | DevProfile, DevChallenge, DevSnippet, ADR, DevRanking |
| `services.py` | Lógica de negocio del dev workspace |
| `forms.py` | Formularios para challenges, snippets, ADRs |
| `decorators.py` | Decoradores de permisos dev |
| `admin.py` | Registro en Django admin |
| `apps.py` | Configuración de la app |
| `urls.py` | Rutas de la app |
| `views/` | Vistas: dashboard, challenges, snippets, ADRs, health, API, ranking |
| `management/` | Comandos de gestión |
| `templates/dev/` | Plantillas HTML |

## Modelos principales

- **DevProfile**: Perfil técnico del desarrollador (GitHub, stack, DevXP)
- **DevChallenge**: Desafíos técnicos con recompensa en DevXP
- **DevSnippet**: Fragmentos de código guardados
- **ADR**: Architecture Decision Records
- **DevRanking**: Rankings de desarrolladores

## Rutas principales

- `/dev/` - Dashboard del dev workspace
- `/dev/challenges/` - Lista de challenges
- `/dev/snippets/` - Gestión de snippets
- `/dev/adr/` - Architecture Decision Records
- `/dev/health/` - Health checks del sistema
- `/dev/api/` - API del dev workspace
- `/dev/ranking/` - Rankings de devs
