"""Lógica de gamificación: niveles y XP por tareas completadas.

Cada 5 tareas completadas se sube 1 nivel (5 XP = 1 nivel).
"""
TASKS_PER_LEVEL = 5
MAX_XP = TASKS_PER_LEVEL


def compute_level_and_xp(completed_count):
    """Calcula nivel y XP a partir de la cantidad de tareas completadas.

    Retorna (level, xp, xp_percent, next_level_xp, xp_needed).
    """
    completed = max(int(completed_count or 0), 0)
    level = completed // TASKS_PER_LEVEL + 1
    xp = completed % TASKS_PER_LEVEL
    xp_percent = xp * (100 // TASKS_PER_LEVEL)
    xp_needed = TASKS_PER_LEVEL - xp
    return level, xp, xp_percent, TASKS_PER_LEVEL, xp_needed
