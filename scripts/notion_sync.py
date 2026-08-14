#!/usr/bin/env python3
"""
Script de sincronización bidireccional con Notion.

Uso:
    python scripts/notion_sync.py push    # Sube roadmap local a Notion
    python scripts/notion_sync.py pull    # Baja de Notion a roadmap.md local
    python scripts/notion_sync.py status  # Muestra estado de sincronización

Requisitos:
    pip install notion-client python-frontmatter pyyaml

Variables de entorno (.env o Render):
    NOTION_TOKEN=secret_xxxxxxxxxxxxx
    NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

try:
    from notion_client import Client
    import frontmatter
except ImportError:
    print("❌ Faltan dependencias: pip install notion-client python-frontmatter pyyaml")
    sys.exit(1)

# Configuración
ROOT = Path(__file__).parent.parent
ROADMAP_FILE = ROOT / "docs" / "roadmap.md"
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_TOKEN or not NOTION_DATABASE_ID:
    print("❌ Configura NOTION_TOKEN y NOTION_DATABASE_ID en variables de entorno")
    sys.exit(1)

notion = Client(auth=NOTION_TOKEN)


def parse_roadmap_md(content: str) -> list[dict]:
    """Parsea roadmap.md y extrae tareas por fase."""
    tasks = []
    current_phase = None
    current_section = None

    lines = content.split("\n")
    for line in lines:
        # Detectar fase: "## FASE 1: ..."
        phase_match = re.match(r"^##\s+FASE\s+(\d+):\s+(.+?)\s*\(Semanas\s+(\d+-\d+)\)", line)
        if phase_match:
            current_phase = {
                "number": int(phase_match.group(1)),
                "name": phase_match.group(2).strip(),
                "weeks": phase_match.group(3).strip(),
            }
            continue

        # Detectar subsección: "### 1.1 Testing"
        section_match = re.match(r"^###\s+(\d+\.\d+)\s+(.+)", line)
        if section_match and current_phase:
            current_section = {
                "code": section_match.group(1),
                "name": section_match.group(2).strip(),
            }
            continue

        # Detectar tarea: "- [ ] Tarea" o "- [x] Tarea"
        task_match = re.match(r"^-\s+\[([ x])\]\s+(.+)", line)
        if task_match and current_phase and current_section:
            tasks.append({
                "phase": current_phase["number"],
                "phase_name": current_phase["name"],
                "phase_weeks": current_phase["weeks"],
                "section": current_section["code"],
                "section_name": current_section["name"],
                "title": task_match.group(2).strip(),
                "done": task_match.group(1) == "x",
            })

    return tasks


def push_to_notion(tasks: list[dict]) -> dict:
    """Sube tareas a Notion (upsert por título único)."""
    results = {"created": 0, "updated": 0, "errors": 0}

    # Obtener páginas existentes para evitar duplicados
    existing = {}
    has_more = True
    start_cursor = None
    while has_more:
        resp = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            start_cursor=start_cursor,
            page_size=100,
        )
        for page in resp["results"]:
            title_prop = page["properties"].get("Tarea", {}).get("title", [])
            if title_prop:
                title = title_prop[0]["plain_text"]
                existing[title] = page["id"]
        has_more = resp["has_more"]
        start_cursor = resp["next_cursor"]

    for task in tasks:
        props = {
            "Tarea": {"title": [{"text": {"content": task["title"]}}]},
            "Fase": {"number": task["phase"]},
            "Fase Nombre": {"rich_text": [{"text": {"content": task["phase_name"]}}]},
            "Semanas": {"rich_text": [{"text": {"content": task["phase_weeks"]}}]},
            "Sección": {"rich_text": [{"text": {"content": task["section"]}}]},
            "Sección Nombre": {"rich_text": [{"text": {"content": task["section_name"]}}]},
            "Estado": {"select": {"name": "Hecho" if task["done"] else "Pendiente"}},
            "Prioridad": {"select": {"name": "Alta" if task["phase"] <= 3 else "Media" if task["phase"] <= 6 else "Baja"}},
            "Última Sync": {"date": {"start": datetime.now().isoformat()}},
        }

        title = task["title"]
        try:
            if title in existing:
                notion.pages.update(page_id=existing[title], properties=props)
                results["updated"] += 1
            else:
                notion.pages.create(parent={"database_id": NOTION_DATABASE_ID}, properties=props)
                results["created"] += 1
        except Exception as e:
            print(f"  ❌ Error con '{title}': {e}")
            results["errors"] += 1

    return results


def pull_from_notion() -> str:
    """Baja tareas de Notion y genera roadmap.md."""
    tasks_by_phase = {}

    has_more = True
    start_cursor = None
    while has_more:
        resp = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            start_cursor=start_cursor,
            page_size=100,
            sorts=[{"property": "Fase", "direction": "ascending"}, {"property": "Sección", "direction": "ascending"}],
        )
        for page in resp["results"]:
            props = page["properties"]
            title = props.get("Tarea", {}).get("title", [{}])[0].get("plain_text", "")
            phase = props.get("Fase", {}).get("number", 0)
            phase_name = props.get("Fase Nombre", {}).get("rich_text", [{}])[0].get("plain_text", "")
            weeks = props.get("Semanas", {}).get("rich_text", [{}])[0].get("plain_text", "")
            section = props.get("Sección", {}).get("rich_text", [{}])[0].get("plain_text", "")
            section_name = props.get("Sección Nombre", {}).get("rich_text", [{}])[0].get("plain_text", "")
            done = props.get("Estado", {}).get("select", {}).get("name", "") == "Hecho"

            if phase not in tasks_by_phase:
                tasks_by_phase[phase] = {"name": phase_name, "weeks": weeks, "sections": {}}
            if section not in tasks_by_phase[phase]["sections"]:
                tasks_by_phase[phase]["sections"][section] = {"name": section_name, "tasks": []}
            tasks_by_phase[phase]["sections"][section]["tasks"].append({"title": title, "done": done})
        has_more = resp["has_more"]
        start_cursor = resp["next_cursor"]

    # Generar markdown
    lines = ["# Roadmap - StarStudy\n", "Plan de desarrollo completo dividido en fases para lograr un producto listo para usuarios reales.\n", "---\n", "\n## Estado Actual ✅\n", "\n**Funcionalidades implementadas:**\n", "- Autenticación por email + rol (Estudiante, Profesor, Personal, Programador)\n", "- Sistema de tareas completo (CRUD, asignación, importancia, archivos, comentarios)\n", "- Horarios personales y de curso (vista tabla + mapa interactivo para programadores)\n", "- Hábitos \"Misión Principal\" (solo Personal, nivel sube al completar)\n", "- Notificaciones automáticas (crear/asignar/completar tareas) + leídas/no leídas\n", "- Vinculación profesor-estudiante (código 6 chars + enlace directo)\n", "- GitHub OAuth para programadores (token encriptado Fernet)\n", "- Gamificación: Niveles + XP (5 tareas = 1 nivel)\n", "- Cache en memoria (LocMem/FileBased) con invalidación inteligente\n", "- Índices DB optimizados (11 índices compuestos)\n", "- Tema \"Noche Estrellada\" responsive (Bootstrap 5.3)\n", "\n---\n"]

    for phase_num in sorted(tasks_by_phase.keys()):
        phase = tasks_by_phase[phase_num]
        lines.append(f"\n## FASE {phase_num}: {phase['name']} (Semanas {phase['weeks']})\n")
        lines.append(f"**Objetivo:** [Completar descripción según fase {phase_num}]\n")
        for section_code in sorted(phase["sections"].keys(), key=lambda x: [int(p) for p in x.split(".")]):
            section = phase["sections"][section_code]
            lines.append(f"\n### {section_code} {section['name']}\n")
            for task in section["tasks"]:
                checkbox = "x" if task["done"] else " "
                lines.append(f"- [{checkbox}] {task['title']}")

    lines.append("\n---\n\n*Última sincronización: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "*\n")
    return "\n".join(lines)


def show_status():
    """Muestra estado de sincronización."""
    local_tasks = parse_roadmap_md(ROADMAP_FILE.read_text(encoding="utf-8"))
    print(f"📄 Tareas locales: {len(local_tasks)}")

    # Contar por fase
    by_phase = {}
    for t in local_tasks:
        by_phase.setdefault(t["phase"], {"total": 0, "done": 0})
        by_phase[t["phase"]]["total"] += 1
        if t["done"]:
            by_phase[t["phase"]]["done"] += 1

    print("\n📊 Progreso por fase:")
    for phase in sorted(by_phase.keys()):
        p = by_phase[phase]
        pct = (p["done"] / p["total"] * 100) if p["total"] else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  Fase {phase}: {p['done']}/{p['total']} ({pct:.0f}%) {bar}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "push":
        print("📤 Subiendo a Notion...")
        tasks = parse_roadmap_md(ROADMAP_FILE.read_text(encoding="utf-8"))
        results = push_to_notion(tasks)
        print(f"✅ Creadas: {results['created']}, Actualizadas: {results['updated']}, Errores: {results['errors']}")

    elif cmd == "pull":
        print("📥 Bajando de Notion...")
        content = pull_from_notion()
        ROADMAP_FILE.write_text(content, encoding="utf-8")
        print(f"✅ Guardado en {ROADMAP_FILE}")

    elif cmd == "status":
        show_status()

    else:
        print(f"❌ Comando desconocido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()