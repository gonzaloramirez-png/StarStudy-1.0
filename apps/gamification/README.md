# App: Gamification

Sistema de gamificación: quizzes, badges, recompensas, rankings y el tip system del profesor.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `models.py` | TipTransaction, Reward, StudentReward, Badge, StudentBadge, Quiz, QuizQuestion, QuizChoice, QuizAttempt, Ranking |
| `forms.py` | Formularios para quiz y recompensas |
| `admin.py` | Registro en Django admin |
| `apps.py` | Configuración de la app |
| `urls.py` | Rutas de la app |
| `views.py` | Vistas de quizzes, badges, rankings, recompensas |
| `management/` | Comandos de gestión |

## Modelos principales

- **TipTransaction**: +XP manual del profesor a estudiante (Tip System)
- **Reward**: Tienda de recompensas canjeables por XP
- **Badge**: Insignias del sistema (primera tarea, rachas, etc.)
- **Quiz**: Quiz autocorregible con opción múltiple
- **Ranking**: Snapshot semanal/mensual de rankings por curso

## Rutas principales

- `/gamificacion/quizzes/` - Lista de quizzes
- `/gamificacion/badges/` - Badges del estudiante
- `/gamificacion/ranking/` - Rankings por curso
- `/gamificacion/recompensas/` - Tienda de recompensas
- `/gamificacion/tip/` - Dar XP a estudiante (profesor)
