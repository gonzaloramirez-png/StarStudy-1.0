# Guía de Configuración Notion ↔ StarStudy

## 1. Crear Integración en Notion

1. Ve a https://www.notion.so/my-integrations
2. Clic en **"New integration"**
3. Nombre: `StarStudy Sync`
4. Logo: opcional
5. Workspace: selecciona tu workspace
6. **Guardar** → Copia el **Internal Integration Token** (empieza con `secret_`)

## 2. Crear Base de Datos en Notion

1. Crea una página nueva en Notion
2. Escribe `/database` y selecciona **"Table - Full page"**
3. Nombra la tabla: `StarStudy Roadmap`
4. Agrega estas **propiedades** (exactamente con estos nombres y tipos):

| Nombre Propiedad | Tipo | Descripción |
|------------------|------|-------------|
| `Tarea` | **Title** | Nombre de la tarea (clave única) |
| `Fase` | **Number** | Número de fase (1-8) |
| `Fase Nombre` | **Text** | Nombre descriptivo de la fase |
| `Semanas` | **Text** | Ej: "1-2", "3-4" |
| `Sección` | **Text** | Código de sección (ej: "1.1") |
| `Sección Nombre` | **Text** | Nombre de la sección |
| `Estado` | **Select** | Opciones: `Pendiente`, `En Progreso`, `Hecho`, `Bloqueado` |
| `Prioridad` | **Select** | Opciones: `Alta`, `Media`, `Baja` |
| `Responsable` | **Person** | (Opcional) Asignado |
| `Estimación` | **Number** | (Opcional) Horas/días |
| `Dependencias` | **Relation** | (Opcional) Relación a otra tarea |
| `Última Sync` | **Date** | Fecha última sincronización |

5. Copia el **Database ID** de la URL:
   `https://notion.so/workspace/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=...`
   El ID es el string de 32 chars entre `/` y `?v=`

## 3. Conectar Integración a la Base de Datos

1. En la página de la base de datos, clic en `•••` (arriba a la derecha)
2. **Connections** → **Add connections**
3. Busca `StarStudy Sync` y confirma

## 4. Configurar Variables de Entorno

### Local (.env)
```bash
cp .env.example .env
# Edita .env y agrega:
NOTION_TOKEN=secret_tu_token_aqui
NOTION_DATABASE_ID=tu_database_id_32_chars
```

### Render (Producción)
En el dashboard de Render → tu servicio → **Environment** → Add:
- `NOTION_TOKEN` = secret_xxx
- `NOTION_DATABASE_ID` = xxxxxxxx...

## 5. Probar Sincronización

```bash
# Activar venv
.\venv\Scripts\activate

# Instalar dependencias nuevas
pip install -r requirements.txt

# Ver estado local
python scripts/notion_sync.py status

# Subir roadmap local → Notion
python scripts/notion_sync.py push

# Bajar Notion → roadmap.md local
python scripts/notion_sync.py pull
```

## 6. Automatizar (Opcional)

### GitHub Actions (push en cada commit a main)
```yaml
# .github/workflows/notion-sync.yml
name: Sync Roadmap to Notion
on:
  push:
    branches: [main]
    paths: ['docs/roadmap.md']
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -r requirements.txt
      - run: python scripts/notion_sync.py push
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
```

### Notion → Git (webhook)
Notion no tiene webhooks nativos. Alternativas:
- **Zapier/Make**: Trigger "Database item updated" → GitHub API commit
- **Cron job**: `python scripts/notion_sync.py pull && git commit -am "sync from notion" && git push`

## 7. Workflow Recomendado

```
Local          Notion           GitHub
  │              │                │
  ├─ edit ──────►│                │
  │  roadmap.md  │                │
  │              │                │
  ├─ push ──────►│ (sync)         │
  │  notion_sync │                │
  │              │                │
  │         ◄────┤ (team edits)   │
  │   pull       │                │
  │              │                │
  ├─ commit ────►│                │
  │  & push      │                │
  │              │                ▼
  │              │           CI/CD deploy
```

## Troubleshooting

| Error | Solución |
|-------|----------|
| `401 Unauthorized` | Token inválido o integración no conectada a la DB |
| `404 Not Found` | Database ID incorrecto |
| `Property "X" does not exist` | Nombres de propiedades deben coincidir exactamente |
| `Duplicate title` | Ya existe una tarea con ese nombre (usa títulos únicos) |

## Estructura de Datos en Notion

Cada fila = una tarea del roadmap. Las fases/secciones se derivan de las propiedades `Fase` y `Sección`. Esto permite:
- Filtrar por fase, estado, prioridad
- Agrupar por fase/sección en vistas Kanban/Table
- Ordenar por prioridad, fecha, responsable
- Dashboards con rollups (conteo tareas por fase, % completado)