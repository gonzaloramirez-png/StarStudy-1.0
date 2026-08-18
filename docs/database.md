# Base de Datos de StarStudy

## Tabla de contenidos

1. [Usuarios](#1-usuarios)
2. [Cursos](#2-cursos)
3. [Tareas](#3-tareas)
4. [Horario](#4-horario)
5. [Hábitos](#5-hábitos)
6. [Gamificación](#6-gamificación)
7. [Desarrolladores (DEV)](#7-desarrolladores-dev)

---

## 1. Usuarios

### accounts_user

Tabla principal de usuarios. Cada persona que usa StarStudy tiene un registro aquí.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único (autogenerado) |
| username | texto | Nombre de usuario |
| email | texto | Correo electrónico (usado para login) |
| password | texto | Contraseña encriptada |
| first_name | texto | Nombre |
| last_name | texto | Apellido |
| role | texto | Rol: STUDENT (Estudiante), TEACHER (Profesor), STAFF (Personal), PROGRAMMER (Programador) |
| code | texto | Código de 6 caracteres para vinculación (solo profesores/personal/programadores) |
| linked_to_id | entero | ID del profesor al que está vinculado (solo estudiantes) |
| github_username | texto | Usuario de GitHub |
| github_token | texto | Token de GitHub encriptado con Fernet |
| pending_email | texto | Email nuevo esperando confirmación |
| avatar | imagen | Foto de perfil |
| xp | entero | Puntos de experiencia acumulados (cada 25 XP = 1 nivel) |
| level | entero | Nivel actual (autocalculado desde XP) |
| badges | JSON | Lista de badges ganados |
| date_joined | fecha | Fecha de registro |
| is_active | booleano | Si la cuenta está activa |

**Relaciones importantes:**
- Un profesor genera un código → muchos estudiantes se vinculan a él (`linked_to`)
- Un usuario tiene muchas notificaciones
- Un usuario tiene muchas tareas asignadas (`assigned_to`) y muchas que él asignó (`assigned_to`)

---

### accounts_notification

Notificaciones que aparecen en la campanita del usuario.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| user_id | entero | A quién va dirigida |
| message | texto | Texto de la notificación (máx. 255 caracteres) |
| link | texto | URL a la que lleva al hacer clic |
| is_read | booleano | Si ya fue leída |
| meta_key | texto | Clave para evitar notificaciones duplicadas |
| created_at | fecha | Cuándo se creó |

---

### accounts_useractivity

Registro de actividad diaria para calcular rachas de días consecutivos.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| user_id | entero | Usuario |
| date | fecha | Día registrado |
| tasks_completed | entero | Tareas completadas ese día |
| xp_earned | entero | XP ganado ese día |
| quizzes_completed | entero | Quizzes completados ese día |
| tips_received | entero | Tips recibidos ese día |
| login_count | entero | Logins ese día |

**Nota:** Solo se crea un registro por usuario por día (unique_together en user+date).

---

### accounts_notificationpreferences

Preferencias de notificación por usuario.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| user_id | entero | Usuario (relación uno a uno) |
| email_deadlines | booleano | Recibir recordatorios de vencimiento por email |
| in_app | booleano | Notificaciones dentro de la app |
| push | booleano | Notificaciones push del navegador |

---

## 2. Cursos

### courses_course

Un curso escolar (ej: "Matemáticas 2024", "Historia 2do A").

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| name | texto | Nombre del curso (máx. 100 caracteres) |
| description | texto | Descripción libre |
| academic_year | texto | Año lectivo (ej: "2024") |
| status | texto | ACTIVE (Activo) o ARCHIVED (Archivado) |
| created_by_id | entero | Profesor que creó el curso |
| created_at | fecha | Fecha de creación |
| archived_at | fecha | Fecha de archivado (si aplica) |

**Relaciones:** Un curso tiene profesores asignados, estudiantes inscriptos, tareas, quizzes, y un código de invitación.

---

### courses_coursecode

Código de invitación para que los estudiantes se inscriban en un curso. Ejemplo: `HU3VK7`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| course_id | entero | Curso al que pertenece (uno a uno) |
| code | texto | Código de 6 caracteres (único en todo el sistema) |
| status | texto | OPEN (Abierto), CLOSED (Cerrado), EXPIRED (Expirado) |
| expires_at | fecha | Cuándo expira (null = nunca) |
| max_uses | entero | Máximo de usos permitidos (0 = ilimitado) |
| current_uses | entero | Cuántas veces se ha usado |
| closed_at | fecha | Cuándo se cerró |

---

### courses_teachercourse

Asignación de un profesor a un curso.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| teacher_id | entero | Profesor |
| course_id | entero | Curso |
| role | texto | TITULAR (dueño principal) o ASISTENTE (ayudante) |
| assigned_by_id | entero | Quién hizo la asignación |
| assigned_at | fecha | Cuándo se asignó |

**Restricción:** Un profesor solo puede estar asignado una vez por curso (unique_together en teacher+course).

---

### courses_studentcourse

Inscripción de un estudiante en un curso.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| student_id | entero | Estudiante |
| course_id | entero | Curso |
| status | texto | ACTIVE (Activo), BLOCKED (Bloqueado), WITHDRAWN (Retirado) |
| enrolled_at | fecha | Cuándo se inscribió |
| enrolled_via_code_id | entero | Código de invitación usado para inscribirse |
| withdrawn_at | fecha | Cuándo se retiró |

**Restricción:** Un estudiante solo puede inscribirse una vez por curso (unique_together en student+course).

---

## 3. Tareas

### tasks_task

Una tarea asignada por un profesor a un estudiante (o una tarea personal del estudiante).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| title | texto | Nombre de la tarea |
| description | texto | Descripción detallada |
| importance | texto | LOW (Baja), MEDIUM (Media), HIGH (Alta), CRITICAL (Crítica) |
| deadline | fecha/hora | Fecha límite de entrega |
| assigned_by_id | entero | Quién la asignó (puede ser el mismo estudiante si es personal) |
| assigned_to_id | entero | A quién va dirigida |
| is_completed | booleano | Si está completada |
| completed_at | fecha | Cuándo se completó |
| is_personal | booleano | Si es tarea personal (no visible para profesores) |
| course_id | entero | Curso al que pertenece (puede ser null) |
| file | archivo | Archivo adjunto (opcional) |
| score | entero | Puntuación 0-100 (la pone el profesor al corregir) |
| status | texto | PENDING (Pendiente), IN_REVIEW (En revisión), CORRECTED (Corregida), RETURNED (Devuelta) |
| corrected_at | fecha | Cuándo se corrigió |
| corrected_by_id | entero | Quién la corrigió |

**Cómo funciona:**
1. Un profesor crea una tarea → se asigna a un estudiante con `status=PENDING`
2. El estudiante la completa → `is_completed=True`, `status=IN_REVIEW`
3. El profesor la corrige → pone un `score` (0-100) y cambia a `status=CORRECTED`
4. El estudiante gana `score` puntos de XP automáticamente
5. El profesor puede devolverla (`status=RETURNED`) si necesita correcciones

---

### tasks_comment

Comentarios en una tarea.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| task_id | entero | Tarea a la que pertenece |
| user_id | entero | Quién escribió el comentario |
| text | texto | Contenido del comentario |
| created_at | fecha | Cuándo se creó |

---

### tasks_commentsnippet

Banco de comentarios reutilizables que un profesor puede usar al corregir.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| teacher_id | entero | Profesor dueño del snippet |
| title | texto | Nombre corto (ej: "Buen trabajo", "Falta profundidad") |
| content | texto | Texto del comentario. Usa `{student_name}` para personalizar |
| category | texto | Categoría: elogio, mejora, instrucción, etc. |
| is_shared | booleano | Si es visible para otros profesores del mismo curso |
| usage_count | entero | Cuántas veces se ha usado |

---

## 4. Horario

### schedule_scheduleentry

Una entrada en el horario semanal del usuario.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| user_id | entero | Dueño del horario |
| day | texto | MON (Lunes), TUE (Martes), WED (Miércoles), THU (Jueves), FRI (Viernes), SAT (Sábado) |
| start_time | hora | Hora de inicio (ej: 08:00) |
| end_time | hora | Hora de fin (ej: 09:30) |
| title | texto | Nombre de la materia/actividad (ej: "Matemáticas") |
| entry_type | texto | SUBJECT (Materia), BREAK (Recreo), LUNCH (Almuerzo) |
| schedule_type | texto | PERSONAL (del usuario) o COURSE (de un curso) |
| course_id | entero | Curso al que pertenece (si es type=COURSE) |

---

### schedule_risktrafficlight

Semáforo de riesgo por estudiante en un curso (lo ve el profesor).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| student_id | entero | Estudiante evaluado |
| course_id | entero | Curso |
| level | texto | GREEN (Verde = sin riesgo), YELLOW (Amarillo = atención), RED (Rojo = riesgo alto) |
| reasons | texto | Motivos del nivel de riesgo |
| auto_calculated | booleano | Si se recalcula automáticamente |
| updated_by_id | entero | Quién lo actualizó (null si es automático) |

**Restricción:** Un registro por estudiante por curso (unique_together en student+course).

---

### schedule_tutoringslot

Horario disponible para tutorías de un profesor.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| teacher_id | entero | Profesor |
| course_id | entero | Curso |
| day | texto | Día de la semana |
| start_time | hora | Hora de inicio |
| end_time | hora | Hora de fin |
| location | texto | Aula o enlace de videollamada |
| max_students | entero | Cuántos estudiantes pueden reservar (1 = individual) |
| is_active | booleano | Si está disponible |

---

### schedule_tutoringappointment

Cita de tutoría reservada por un estudiante.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| slot_id | entero | Horario del que se reservó |
| student_id | entero | Estudiante que reservó |
| status | texto | PENDING (Pendiente), CONFIRMED (Confirmada), CANCELLED (Cancelada), COMPLETED (Realizada) |
| notes | texto | Motivo de la tutoría |
| confirmed_at | fecha | Cuándo confirmó el profesor |
| completed_at | fecha | Cuándo se realizó |

**Restricción:** Un estudiante solo puede reservar una vez por slot (unique_together en slot+student).

---

## 5. Hábitos

### habits_habit

Un hábito diario que el estudiante quiere desarrollar.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| user_id | entero | Dueño del hábito |
| title | texto | Nombre del hábito (ej: "Leer 30 minutos") |
| category | texto | FOCUS (Enfoque/azul), ESSENTIAL (Esencial/amarillo), URGENT (Urgente/rojo), WELLNESS (Bienestar/verde) |
| start_time | hora | Hora de inicio sugerida |
| end_time | hora | Hora de fin sugerida |
| level | entero | Nivel del hábito (sube cada vez que se completa) |
| created_at | fecha | Cuándo se creó |

**Cómo funciona:** Cada vez que el estudiante marca un hábito como completado, su `level` sube en 1. El nivel se muestra como indicador de constancia.

---

### habits_habitcompletion

Registro de que un hábito se completó en un día.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| habit_id | entero | Hábito completado |
| date | fecha | Día en que se completó |
| completed_at | fecha/hora | Momento exacto de la marca |

**Restricción:** Solo un registro por hábito por día (unique_together en habit+date). No se puede marcar dos veces el mismo día.

---

## 6. Gamificación

### gamification_tiptransaction

Cuando un profesor le da XP extra a un estudiante (tip manual).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| teacher_id | entero | Profesor que da el tip |
| student_id | entero | Estudiante que recibe |
| course_id | entero | Curso en el que aplica |
| xp_amount | entero | Cuántos XP da (default: 5) |
| reason | texto | PARTICIPATION (Gran participación), HELP_PEER (Ayudó a compañero), CREATIVE (Solución creativa), EFFORT (Esfuerzo extra), LEADERSHIP (Liderazgo), CUSTOM (Otro) |
| custom_reason | texto | Motivo personalizado (si reason=CUSTOM) |
| created_at | fecha | Cuándo se dio el tip |

---

### gamification_reward

Tienda de recompensas canjeables con XP.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| course_id | entero | Curso al que pertenece |
| name | texto | Nombre de la recompensa (ej: "Día extra de plazo") |
| description | texto | Descripción |
| type | texto | EXTENSION (Día extra), SKIP_TASK (Saltar tarea), BONUS_XP (Bonus XP), BADGE (Badge exclusivo), PRIVILEGE (Privilegio), CUSTOM (Personalizada) |
| xp_cost | entero | Cuántos XP cuesta canjearla |
| icon | texto | Icono de Bootstrap Icons |
| max_claims | entero | Cuántas veces se puede canjear (0 = ilimitado) |
| current_claims | entero | Cuántas veces se ha canjeado |
| is_active | booleano | Si está disponible en la tienda |
| created_by_id | entero | Quién la creó |

---

### gamification_studentreward

Registro de un canje de recompensa.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| student_id | entero | Quién canjeó |
| reward_id | entero | Qué recompensa canjeó |
| course_id | entero | Curso |
| xp_spent | entero | XP gastado (capturado al momento del canje) |
| is_used | booleano | Si ya se usó la recompensa |
| used_at | fecha | Cuándo se usó |

---

### gamification_badge

Insignia que se puede ganar (ej: "Primera tarea completada", "7 días de racha").

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| name | texto | Nombre único (ej: "Primer Paso") |
| description | texto | Descripción de cómo se gana |
| category | texto | ACADEMIC (Académica), SOCIAL (Social), CONSISTENCY (Constancia), ACHIEVEMENT (Logro), SPECIAL (Especial) |
| icon | texto | Icono de Bootstrap Icons |
| color | texto | Color CSS |
| xp_reward | entero | XP extra que da al ganarla |
| is_secret | booleano | Si es secreta (no visible hasta ganarla) |
| created_by_id | entero | Quién la creó |

---

### gamification_studentbadge

Registro de un badge ganado por un estudiante.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| student_id | entero | Estudiante |
| badge_id | entero | Badge ganado |
| course_id | entero | Curso en el que lo ganó |
| earned_at | fecha | Cuándo lo ganó |
| earned_by_id | entero | Quién se lo dio (null si es automático) |
| xp_awarded | entero | XP que ganó con el badge |

**Restricción:** Un estudiante solo puede ganar un badge una vez por curso (unique_together en student+badge+course).

---

### gamification_quiz

Quiz autocorregible para un curso.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| course_id | entero | Curso al que pertenece |
| title | texto | Nombre del quiz |
| description | texto | Descripción |
| instructions | texto | Instrucciones para el estudiante |
| xp_reward | entero | XP al completar con nota mínima (default: 10) |
| passing_score | entero | Nota mínima para aprobar, 0-100 (default: 60) |
| time_limit | entero | Límite en minutos (0 = sin límite) |
| max_attempts | entero | Máximo de intentos (default: 3) |
| shuffle_questions | booleano | Si se mezclan las preguntas |
| shuffle_choices | booleano | Si se mezclan las opciones |
| is_active | booleano | Si está disponible |
| available_from | fecha | Disponible desde |
| available_until | fecha | Disponible hasta |
| created_by_id | entero | Quién lo creó |

---

### gamification_quizquestion

Pregunta de un quiz.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| quiz_id | entero | Quiz al que pertenece |
| order | entero | Orden de aparición |
| text | texto | Texto de la pregunta |
| type | texto | SINGLE (Opción única), MULTIPLE (Opción múltiple), TF (Verdadero/Falso) |
| points | entero | Puntos que vale (default: 1) |
| explanation | texto | Explicación mostrada tras responder |

---

### gamification_quizchoice

Opción de respuesta de una pregunta.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| question_id | entero | Pregunta a la que pertenece |
| order | entero | Orden de aparición |
| text | texto | Texto de la opción |
| is_correct | booleano | Si es la respuesta correcta |

---

### gamification_quizattempt

Intento de un estudiante en un quiz.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| quiz_id | entero | Quiz |
| student_id | entero | Estudiante |
| status | texto | IN_PROGRESS (En progreso), SUBMITTED (Enviado), GRADED (Calificado) |
| started_at | fecha | Cuándo empezó |
| submitted_at | fecha | Cuándo lo envió |
| score | decimal | Porcentaje de acierto (0-100) |
| xp_earned | entero | XP ganado (0 si no aprobó) |
| passed | booleano | Si aprobó |
| answers | JSON | Respuestas: `{id_pregunta: [id_opciones]}` |
| time_spent | entero | Tiempo invertido en segundos |

**Cómo funciona:**
1. El estudiante empieza el quiz → `status=IN_PROGRESS`
2. Envía las respuestas → se autocorrige automáticamente
3. Si `score >= passing_score` → gana `xp_reward` y se notifica
4. Si no aprueba → no gana XP pero puede reintentar (si quedan intentos)

---

### gamification_ranking

Snapshot de ranking por curso (semanal o mensual).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| course_id | entero | Curso |
| period | texto | WEEKLY (Semanal) o MONTHLY (Mensual) |
| student_id | entero | Estudiante |
| position | entero | Posición en el ranking (1 = mejor) |
| xp_earned | entero | XP ganado en el período |
| total_xp | entero | XP acumulado total |
| tasks_completed | entero | Tareas completadas en el período |
| period_start | fecha | Inicio del período |
| period_end | fecha | Fin del período |

**Cómo se calcula el XP de un período:** Suma de tareas completadas + Tips recibidos + Quizzes aprobados + Badges ganados, todo dentro del rango de fechas del período.

---

## 7. Desarrolladores (DEV)

Solo accesible para usuarios con rol PROGRAMMER.

### dev_devprofile

Perfil técnico del desarrollador.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| user_id | entero | Usuario (uno a uno) |
| github_handle | texto | Usuario de GitHub |
| preferred_stack | JSON | Stack tecnológico preferido |
| total_dev_xp | entero | XP de desarrollo acumulado |
| current_dev_level | entero | Nivel de desarrollador |
| focus_mode_active | booleano | Si tiene modo foco activado |
| api_token | texto | Token de API (autogenerado) |

---

### dev_devchallenge

Desafío de código para resolver.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| title | texto | Nombre del desafío |
| description | texto | Enunciado |
| difficulty | texto | EASY (Fácil), MEDIUM (Medio), HARD (Difícil) |
| category | texto | REFACTORING, SQL_OPTIMIZATION, SECURITY_OWASP, ARCHITECTURE |
| initial_code | texto | Código inicial para modificar |
| test_cases | JSON | Casos de prueba |
| xp_reward | entero | XP por resolverlo |
| frequency | texto | DAILY (Diario), EVERY_3_DAYS (Cada 3 días), WEEKLY (Semanal) |

---

### dev_devsubmission

Envío de solución a un desafío.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| dev_profile_id | entero | Desarrollador |
| challenge_id | entero | Desafío |
| submitted_code | texto | Código enviado |
| execution_time_ms | entero | Tiempo de ejecución en ms |
| memory_used_kb | decimal | Memoria usada en KB |
| status | texto | PASSED (Aprobado), FAILED (Falló), ERROR (Error) |
| xp_earned | entero | XP ganado |

**Restricción:** Un desarrollador solo puede enviar una solución por desafío (unique_together en dev_profile+challenge).

---

### dev_devsnippet

Fragmento de código guardado por el desarrollador.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| dev_profile_id | entero | Desarrollador |
| title | texto | Nombre del snippet |
| code | texto | Código fuente |
| language | texto | Lenguaje (python, javascript, etc.) |
| tags | JSON | Etiquetas para buscar |
| is_private | booleano | Si es privado o público |

---

### dev_devlog

Log de salud del servidor.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| service_name | texto | Nombre del servicio |
| status | texto | HEALTHY (Saludable), DEGRADED (Degradado), DOWN (Caído) |
| response_time_ms | entero | Tiempo de respuesta |
| logs_trace | texto | Traza de logs |
| endpoint | texto | URL del endpoint verificado |

---

### dev_devadr

Architecture Decision Record — documentos de decisiones técnicas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| title | texto | Título de la decisión |
| context | texto | Contexto del problema |
| decision | texto | Decisión tomada |
| consequences | texto | Consecuencias de la decisión |
| status | texto | PROPOSED (Propuesto), ACCEPTED (Aceptado), DEPRECATED (Deprecado) |
| author_id | entero | Quién lo escribió |

---

### dev_devpinglog

Log de health check / warm-up ping.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | entero | Identificador único |
| endpoint | texto | URL verificada |
| status_code | entero | Código HTTP (200, 404, 500, etc.) |
| response_time_ms | entero | Tiempo de respuesta |

---

## Diagrama de relaciones (simplificado)

```
User (1) ──── (N) Notification
User (1) ──── (N) UserActivity
User (1) ──── (1) NotificationPreferences
User (1) ──── (N) Task (como assigned_to)
User (1) ──── (N) Task (como assigned_by)
User (1) ──── (N) Habit
User (1) ──── (N) ScheduleEntry
User (1) ──── (1) DevProfile

Course (1) ──── (1) CourseCode
Course (1) ──── (N) TeacherCourse ──── User
Course (1) ──── (N) StudentCourse ──── User
Course (1) ──── (N) Task
Course (1) ──── (N) Quiz ──── QuizQuestion ──── QuizChoice
Course (1) ──── (N) Ranking
Course (1) ──── (N) Reward ──── StudentReward ──── User
Course (1) ──── (N) TipTransaction
Course (1) ──── (N) RiskTrafficLight

Task (1) ──── (N) Comment ──── User
Habit (1) ──── (N) HabitCompletion
Quiz (1) ──── (N) QuizAttempt ──── User

DevProfile (1) ──── (N) DevSubmission ──── DevChallenge
DevProfile (1) ──── (N) DevSnippet
```

---

## Fuentes de XP

Un estudiante gana XP de 4 maneras:

1. **Tareas corregidas** → El profesor pone un score (0-100) y el estudiante gana esos XP
2. **Tips manuales** → El profesor le da XP extra por participación, esfuerzo, etc.
3. **Quizzes aprobados** → Si aprueba (>= nota mínima), gana el XP del quiz
4. **Badges ganados** → Al ganar una insignia, recibe XP bonus

**Cada 25 XP = 1 nivel.** El nivel se actualiza automáticamente.
