"""Models de schedule: Entrada de horario, Semáforo de riesgo, Agenda de tutorías.

- ScheduleEntry: entrada horaria con día (Lun-Vie), hora inicio/fin, título,
  tipo de entrada (Materia/Recreo/Almuerzo) y tipo de horario (Personal/Curso).
  El schedule_type se asigna automáticamente en la vista (no en el formulario).
- RiskTrafficLight: Semáforo de riesgo por estudiante en un curso (Verde/Amarillo/Rojo).
  Calculado automáticamente o editable por profesor.
- TutoringSlot: Horario disponible para tutorías del profesor.
- TutoringAppointment: Cita de tutoría reservada por estudiante.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class ScheduleEntry(models.Model):
    """Entrada de horario semanal."""
    class Day(models.TextChoices):
        MONDAY = 'MON', 'Lunes'
        TUESDAY = 'TUE', 'Martes'
        WEDNESDAY = 'WED', 'Miércoles'
        THURSDAY = 'THU', 'Jueves'
        FRIDAY = 'FRI', 'Viernes'

    class EntryType(models.TextChoices):
        SUBJECT = 'SUBJECT', 'Materia'
        BREAK = 'BREAK', 'Recreo'
        LUNCH = 'LUNCH', 'Almuerzo'

    class ScheduleType(models.TextChoices):
        PERSONAL = 'PERSONAL', 'Personal'
        COURSE = 'COURSE', 'Curso'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedule_entries')
    day = models.CharField(max_length=3, choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    title = models.CharField(max_length=200)
    entry_type = models.CharField(max_length=10, choices=EntryType.choices, default=EntryType.SUBJECT)
    schedule_type = models.CharField(max_length=10, choices=ScheduleType.choices, default=ScheduleType.PERSONAL)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True, related_name='schedule_entries')

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time}-{self.end_time} {self.title}"


class RiskTrafficLight(models.Model):
    """Semáforo de riesgo por estudiante en un curso: Verde/Amarillo/Rojo."""
    class RiskLevel(models.TextChoices):
        GREEN = 'GREEN', 'Verde (Sin riesgo)'
        YELLOW = 'YELLOW', 'Amarillo (Atención)'
        RED = 'RED', 'Rojo (Riesgo alto)'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='risk_lights')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='risk_lights')
    level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.GREEN, db_index=True)
    reasons = models.TextField(blank=True, help_text='Motivos del nivel de riesgo')
    auto_calculated = models.BooleanField(default=True, help_text='Si True, se recalcula automáticamente')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='risk_updates')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['level', 'student__email']

    def __str__(self):
        return f"{self.student.email} - {self.course.name}: {self.get_level_display()}"

    def get_badge_class(self):
        return {'GREEN': 'bg-success', 'YELLOW': 'bg-warning text-dark', 'RED': 'bg-danger'}[self.level]


class TutoringSlot(models.Model):
    """Horario disponible para tutorías del profesor."""
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutoring_slots')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='tutoring_slots')
    day = models.CharField(max_length=3, choices=ScheduleEntry.Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=100, blank=True, help_text='Aula, enlace videollamada, etc.')
    max_students = models.PositiveIntegerField(default=1, help_text='Máx. estudiantes por slot (1=individual)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.teacher.email} - {self.get_day_display()} {self.start_time}-{self.end_time}"

    @property
    def available_spots(self):
        from django.db.models import Count
        booked = self.appointments.filter(status__in=[TutoringAppointment.Status.CONFIRMED, TutoringAppointment.Status.PENDING]).count()
        return max(0, self.max_students - booked)


class TutoringAppointment(models.Model):
    """Cita de tutoría reservada por estudiante."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente confirmación'
        CONFIRMED = 'CONFIRMED', 'Confirmada'
        CANCELLED = 'CANCELLED', 'Cancelada'
        COMPLETED = 'COMPLETED', 'Realizada'

    slot = models.ForeignKey(TutoringSlot, on_delete=models.CASCADE, related_name='appointments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tutoring_appointments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    notes = models.TextField(blank=True, help_text='Motivo de la tutoría, temas a tratar')
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['slot', 'student']

    def __str__(self):
        return f"{self.student.email} - {self.slot} ({self.get_status_display()})"

    def confirm(self):
        self.status = self.Status.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save(update_fields=['status', 'confirmed_at'])

    def cancel(self):
        self.status = self.Status.CANCELLED
        self.save(update_fields=['status'])

    def complete(self):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
