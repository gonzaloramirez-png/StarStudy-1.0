"""Models de courses: Curso, Código de invitación, Asignación profesor-curso, Estudiante-curso.

- Course: Curso con nombre, descripción, año lectivo, estado (activo/archivado).
- CourseCode: Código dinámico de 6 caracteres por curso, regenerable/cerrable.
- TeacherCourse: Vinculación profesor-curso con rol (TITULAR/ASISTENTE).
- StudentCourse: Inscripción estudiante-curso con estado (ACTIVO/BLOQUEADO/RETIRADO).
"""
import secrets
import string
from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_course_code():
    """Genera código alfanumérico de 6 caracteres para invitación a curso."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))


class Course(models.Model):
    """Curso escolar con gestión de estado y código de invitación."""
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        ARCHIVED = 'ARCHIVED', 'Archivado'

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    academic_year = models.CharField(max_length=20, default='2024')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'academic_year']),
            models.Index(fields=['created_by', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=['status', 'archived_at', 'updated_at'])
        # Cerrar código de invitación si existe
        if hasattr(self, 'invite_code'):
            self.invite_code.close()

    def restore(self):
        self.status = self.Status.ACTIVE
        self.archived_at = None
        self.save(update_fields=['status', 'archived_at', 'updated_at'])

    @property
    def teacher_count(self):
        return self.teacher_assignments.count()

    def clone(self, new_name=None, academic_year=None, created_by=None):
        """Clona el curso con su estructura de tareas (sin estudiantes ni notas).

        Returns: Course (el nuevo curso clonado)
        """
        from apps.tasks.models import Task

        new_course = Course.objects.create(
            name=new_name or f"{self.name} (Copia)",
            description=self.description,
            academic_year=academic_year or self.academic_year,
            status=self.Status.ACTIVE,
            created_by=created_by or self.created_by,
        )
        if hasattr(self, 'invite_code'):
            from apps.courses.models import CourseCode
            CourseCode.objects.create(course=new_course, code=generate_course_code())

        # Clonar tareas (estructura, sin estudiantes ni calificaciones)
        old_tasks = Task.objects.filter(course=self).order_by('deadline')
        task_map = {}
        for old_task in old_tasks:
            new_task = Task.objects.create(
                title=old_task.title,
                description=old_task.description,
                importance=old_task.importance,
                deadline=old_task.deadline,
                assigned_by=old_task.assigned_by,
                assigned_to=old_task.assigned_to,
                is_personal=old_task.is_personal,
                course=new_course,
                # No copiar: score, status, corrected_at, is_completed, file
            )
            task_map[old_task.pk] = new_task

        return new_course

    @property
    def student_count(self):
        return self.student_enrollments.filter(status=StudentCourse.Status.ACTIVE).count()


class CourseCode(models.Model):
    """Código de invitación dinámico por curso (regenerable/cerrable)."""
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Abierto'
        CLOSED = 'CLOSED', 'Cerrado'
        EXPIRED = 'EXPIRED', 'Expirado'

    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='invite_code')
    code = models.CharField(max_length=6, unique=True, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=0, help_text='0 = ilimitado')
    current_uses = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_course_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.name} - {self.code} ({self.get_status_display()})"

    def is_valid(self):
        if self.status != self.Status.OPEN:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status'])
            return False
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status'])
            return False
        return True

    def use_code(self):
        """Incrementa contador de usos."""
        self.current_uses += 1
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            self.status = self.Status.EXPIRED
        self.save(update_fields=['current_uses', 'status', 'updated_at'])

    def regenerate(self):
        """Genera nuevo código manteniendo configuración."""
        old_code = self.code
        while True:
            new_code = generate_course_code()
            if not CourseCode.objects.filter(code=new_code).exists():
                self.code = new_code
                self.status = self.Status.OPEN
                self.closed_at = None
                self.current_uses = 0
                self.save(update_fields=['code', 'status', 'closed_at', 'current_uses', 'updated_at'])
                break
        return old_code

    def close(self):
        """Cierra el código de invitación."""
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at', 'updated_at'])

    def open(self):
        """Reabre el código si no está expirado."""
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = self.Status.EXPIRED
        else:
            self.status = self.Status.OPEN
        self.closed_at = None
        self.save(update_fields=['status', 'closed_at', 'updated_at'])


class TeacherCourse(models.Model):
    """Asignación de profesor a curso con rol específico."""
    class Role(models.TextChoices):
        TITULAR = 'TITULAR', 'Titular'
        ASISTENTE = 'ASISTENTE', 'Asistente'

    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='teacher_assignments')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TITULAR)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_teachers')

    class Meta:
        unique_together = ['teacher', 'course']
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.teacher.email} - {self.course.name} ({self.get_role_display()})"


class StudentCourse(models.Model):
    """Inscripción de estudiante en curso."""
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        BLOCKED = 'BLOCKED', 'Bloqueado'
        WITHDRAWN = 'WITHDRAWN', 'Retirado'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_via_code = models.ForeignKey(CourseCode, on_delete=models.SET_NULL, null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['student', 'status']),
        ]

    def __str__(self):
        return f"{self.student.email} - {self.course.name} ({self.get_status_display()})"

    def withdraw(self):
        self.status = self.Status.WITHDRAWN
        self.withdrawn_at = timezone.now()
        self.save(update_fields=['status', 'withdrawn_at'])

    def block(self):
        self.status = self.Status.BLOCKED
        self.save(update_fields=['status'])

    def activate(self):
        self.status = self.Status.ACTIVE
        self.withdrawn_at = None
        self.save(update_fields=['status', 'withdrawn_at'])