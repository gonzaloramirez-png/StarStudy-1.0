"""Models de tasks: Tarea, Comentario, Snippet de corrección.

- Task: Tarea con importancia (LOW/MEDIUM/HIGH/CRITICAL), deadline, asignación
  bidireccional (assigned_by → assigned_to), flag is_personal para tareas privadas,
  y 3 índices compuestos para consultas frecuentes.
  NUEVO: score (0-100), status (PENDING/IN_REVIEW/CORRECTED/RETURNED), corrected_at.
- Comment: Comentarios en tareas, ordenados cronológicamente.
- CommentSnippet: Banco de comentarios reutilizables (snippets) por profesor.
"""
from django.conf import settings
from django.db import models
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone


class Task(models.Model):
    class Importance(models.TextChoices):
        LOW = 'LOW', 'Baja'
        MEDIUM = 'MEDIUM', 'Media'
        HIGH = 'HIGH', 'Alta'
        CRITICAL = 'CRITICAL', 'Crítica'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        IN_REVIEW = 'IN_REVIEW', 'En revisión'
        CORRECTED = 'CORRECTED', 'Corregida'
        RETURNED = 'RETURNED', 'Devuelta'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    importance = models.CharField(max_length=20, choices=Importance.choices, default=Importance.MEDIUM, db_index=True)
    deadline = models.DateTimeField(db_index=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_tasks')
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_personal = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to='task_files/', blank=True, null=True)

    # Curso asociado (para filtrado por curso)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')

    # Corrección/Calificación
    score = models.PositiveSmallIntegerField(null=True, blank=True, help_text='Puntuación 0-100')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    corrected_at = models.DateTimeField(null=True, blank=True)
    corrected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='corrected_tasks')

    class Meta:
        ordering = [
            Case(
                When(importance='CRITICAL', then=Value(0)),
                When(importance='HIGH', then=Value(1)),
                When(importance='MEDIUM', then=Value(2)),
                When(importance='LOW', then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            ),
            'deadline',
        ]
        indexes = [
            models.Index(fields=['assigned_to', 'is_personal', 'is_completed'], name='idx_task_to_pers_comp'),
            models.Index(fields=['assigned_by', 'is_personal', 'is_completed'], name='idx_task_by_pers_comp'),
            models.Index(fields=['deadline', 'is_completed'], name='idx_task_deadline_comp'),
            models.Index(fields=['assigned_by', 'status'], name='idx_task_by_status'),
        ]

    def __str__(self):
        return f"{self.title} - {self.assigned_to.email}"

    def mark_corrected(self, user, score=None):
        self.status = self.Status.CORRECTED
        self.corrected_at = timezone.now()
        self.corrected_by = user
        if score is not None:
            self.score = score
        self.save(update_fields=['status', 'corrected_at', 'corrected_by', 'score', 'updated_at'])

    def mark_returned(self, user):
        self.status = self.Status.RETURNED
        self.corrected_by = user
        self.save(update_fields=['status', 'corrected_by', 'updated_at'])


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.email} - {self.text[:50]}"


class CommentSnippet(models.Model):
    """Banco de comentarios reutilizables (snippets) por profesor."""
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_snippets')
    title = models.CharField(max_length=100, help_text='Nombre corto para identificar el snippet')
    content = models.TextField(help_text='Texto del comentario. Usa {student_name} para personalizar.')
    category = models.CharField(max_length=50, blank=True, help_text='Categoría: elogio, mejora, instrucción, etc.')
    is_shared = models.BooleanField(default=False, help_text='Visible para otros profesores del mismo curso')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'title']
        unique_together = ['teacher', 'title']

    def __str__(self):
        return f"{self.teacher.email} - {self.title}"

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
