"""Modelos del módulo DEV Workspace."""
import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class DevProfile(models.Model):
    """Perfil técnico del desarrollador."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dev_profile',
    )
    github_handle = models.CharField(max_length=100, blank=True, default='')
    preferred_stack = models.JSONField(default=list, blank=True)
    total_dev_xp = models.PositiveIntegerField(default=0)
    current_dev_level = models.PositiveIntegerField(default=1)
    focus_mode_active = models.BooleanField(default=False)
    api_token = models.CharField(max_length=64, unique=True, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dev Profile'
        verbose_name_plural = 'Dev Profiles'

    def __str__(self):
        return f"DEV: {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.api_token:
            self.api_token = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def add_dev_xp(self, amount):
        """Agrega DevXP y calcula nivel (25 XP = 1 nivel)."""
        self.total_dev_xp += amount
        new_level = (self.total_dev_xp // 25) + 1
        leveled_up = new_level > self.current_dev_level
        self.current_dev_level = new_level
        self.save(update_fields=['total_dev_xp', 'current_dev_level'])
        return leveled_up

    @property
    def xp_progress(self):
        """Progreso al siguiente nivel (0-100)."""
        return (self.total_dev_xp % 25) / 25 * 100


class DevChallenge(models.Model):
    """Desafío de código para desarrolladores."""

    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Fácil'
        MEDIUM = 'MEDIUM', 'Medio'
        HARD = 'HARD', 'Difícil'

    class Category(models.TextChoices):
        REFACTORING = 'REFACTORING', 'Refactoring'
        SQL_OPTIMIZATION = 'SQL_OPTIMIZATION', 'Optimización SQL'
        SECURITY_OWASP = 'SECURITY_OWASP', 'Seguridad OWASP'
        ARCHITECTURE = 'ARCHITECTURE', 'Arquitectura'

    class Frequency(models.TextChoices):
        DAILY = 'DAILY', 'Diario'
        EVERY_3_DAYS = 'EVERY_3_DAYS', 'Cada 3 días'
        WEEKLY = 'WEEKLY', 'Semanal'

    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices)
    category = models.CharField(max_length=20, choices=Category.choices)
    initial_code = models.TextField(blank=True, default='')
    test_cases = models.JSONField(default=list)
    xp_reward = models.PositiveIntegerField(default=25)
    frequency = models.CharField(max_length=12, choices=Frequency.choices, default=Frequency.DAILY)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.difficulty}] {self.title}"


class DevSubmission(models.Model):
    """Envío de solución a un desafío."""

    class Status(models.TextChoices):
        PASSED = 'PASSED', 'Aprobado'
        FAILED = 'FAILED', 'Falló'
        ERROR = 'ERROR', 'Error'

    dev_profile = models.ForeignKey(DevProfile, on_delete=models.CASCADE, related_name='submissions')
    challenge = models.ForeignKey(DevChallenge, on_delete=models.CASCADE, related_name='submissions')
    submitted_code = models.TextField()
    execution_time_ms = models.PositiveIntegerField(null=True, blank=True)
    memory_used_kb = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices)
    xp_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['dev_profile', 'challenge']

    def __str__(self):
        return f"{self.dev_profile.user.email} -> {self.challenge.title} [{self.status}]"


class DevSnippet(models.Model):
    """Fragmento de código del desarrollador."""
    dev_profile = models.ForeignKey(DevProfile, on_delete=models.CASCADE, related_name='snippets')
    title = models.CharField(max_length=200)
    code = models.TextField()
    language = models.CharField(max_length=50, blank=True, default='python')
    tags = models.JSONField(default=list, blank=True)
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class DevLog(models.Model):
    """Log de salud del servidor."""

    class Status(models.TextChoices):
        HEALTHY = 'HEALTHY', 'Saludable'
        DEGRADED = 'DEGRADED', 'Degradado'
        DOWN = 'DOWN', 'Caído'

    service_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=Status.choices)
    response_time_ms = models.PositiveIntegerField(default=0)
    logs_trace = models.TextField(blank=True, default='')
    endpoint = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dev Log'
        verbose_name_plural = 'Dev Logs'

    def __str__(self):
        return f"{self.service_name} [{self.status}] {self.created_at:%Y-%m-%d %H:%M}"


class DevADR(models.Model):
    """Architecture Decision Record."""

    class Status(models.TextChoices):
        PROPOSED = 'PROPOSED', 'Propuesto'
        ACCEPTED = 'ACCEPTED', 'Aceptado'
        DEPRECATED = 'DEPRECATED', 'Deprecado'

    title = models.CharField(max_length=200)
    context = models.TextField(help_text='Contexto del problema')
    decision = models.TextField(help_text='Decisión tomada')
    consequences = models.TextField(help_text='Consecuencias de la decisión')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PROPOSED)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dev_adrs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ADR'
        verbose_name_plural = 'ADRs'

    def __str__(self):
        return f"[{self.status}] {self.title}"


class DevPingLog(models.Model):
    """Log de health check / warm-up ping."""
    endpoint = models.CharField(max_length=200)
    status_code = models.PositiveIntegerField()
    response_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ping {self.endpoint} -> {self.status_code} ({self.response_time_ms}ms)"
