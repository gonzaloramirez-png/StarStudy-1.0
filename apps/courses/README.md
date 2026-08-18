# App: Courses

Gestión de cursos escolares: creación, inscripción, códigos de invitación y archivado.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `models.py` | Course, CourseCode, TeacherCourse, StudentCourse |
| `admin.py` | Registro en Django admin |
| `apps.py` | Configuración de la app |
| `urls.py` | Rutas de la app |
| `views/` | Vistas: CRUD cursos, inscripción, clonado, códigos |
| `templates/courses/` | Plantillas HTML |

## Modelos principales

- **Course**: Curso con nombre, año lectivo, estado (activo/archivado)
- **CourseCode**: Código alfanumérico de 6 caracteres para inscripción
- **TeacherCourse**: Vinculación profesor-curso (TITULAR/ASISTENTE)
- **StudentCourse**: Inscripción estudiante-curso (ACTIVO/BLOQUEADO/RETIRADO)

## Rutas principales

- `/cursos/` - Lista de cursos
- `/cursos/nuevo/` - Crear curso (profesor)
- `/cursos/<id>/` - Detalle del curso
- `/cursos/clonar/<id>/` - Clonar curso
- `/cursos/inscribirse/<code>/` - Inscribirse con código
- `/cursos/invitar/<id>/` - Gestionar código de invitación
