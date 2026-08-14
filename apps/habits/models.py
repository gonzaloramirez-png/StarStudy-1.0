"""Models de habits: Hábito y Registro de completación.

- Habit: hábito diario con título, horario de inicio/fin, y nivel que sube al completarse.
  Ordenado por nivel descendente. Usa timezone.localdate() para fecha actual.
- HabitCompletion: registro de completación diaria (unique_together habit+date).
  Evita marcar el mismo hábito dos veces el mismo día.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Habit(models.Model):
    """Hábito diario con colorimetría por categoría.

    Categorías (colorimetría de hábitos):
    - FOCUS: azul — hábitos clave/no negociables (leer, meditar, proyecto principal).
    - ESSENTIAL: amarillo — rutina diaria y mantenimiento (ejercicio, limpieza, correos).
    - URGENT: rojo — urgencias, fechas límite estrictas o malos hábitos a eliminar.
    - WELLNESS: verde — bienestar, descanso, recreación y autocuidado.
    El color de cada tarjeta se asigna automáticamente desde la categoría.
    """

    class Category(models.TextChoices):
        FOCUS = 'FOCUS', 'Enfoque'
        ESSENTIAL = 'ESSENTIAL', 'Esencial'
        URGENT = 'URGENT', 'Urgente'
        WELLNESS = 'WELLNESS', 'Bienestar'

    CATEGORY_COLORS = {
        Category.FOCUS: 'primary',
        Category.ESSENTIAL: 'warning',
        Category.URGENT: 'danger',
        Category.WELLNESS: 'success',
    }

    CATEGORY_ICONS = {
        Category.FOCUS: 'bi-bullseye',
        Category.ESSENTIAL: 'bi-sun',
        Category.URGENT: 'bi-alarm',
        Category.WELLNESS: 'bi-flower1',
    }

    CATEGORY_LABELS = {
        Category.FOCUS: 'Enfoque y Hábitos Clave',
        Category.ESSENTIAL: 'Esenciales / Rutina Diaria',
        Category.URGENT: 'Urgencias / Alto Impacto',
        Category.WELLNESS: 'Bienestar / Secundarios',
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='habits')
    title = models.CharField(max_length=200)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.ESSENTIAL,
        db_index=True,
    )
    start_time = models.TimeField(default='00:00')
    end_time = models.TimeField(default='00:00')
    level = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-level', 'title']

    @property
    def color(self):
        return self.CATEGORY_COLORS.get(self.category, 'secondary')

    @property
    def icon(self):
        return self.CATEGORY_ICONS.get(self.category, 'bi-star')

    @property
    def category_label(self):
        return self.CATEGORY_LABELS.get(self.category, self.get_category_display())

    def completed_today(self):
        return self.completions.filter(date=timezone.localdate()).exists()

    def total_completions(self):
        return self.completions.count()

    def __str__(self):
        return f"{self.title} (nivel {self.level})"


class HabitCompletion(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='completions')
    date = models.DateField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['habit', 'date']

    def __str__(self):
        return f"{self.habit.title} - {self.date}"
