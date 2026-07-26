"""Models de accounts: Usuario y Notificaciones.

- User: Extiende AbstractUser con roles (Estudiante, Profesor, Personal, Programador, Admin),
  sistema de vinculación entre profesores y estudiantes, código de invitación,
  y encriptación de token de GitHub con Fernet.
- Notification: Notificaciones del sistema con cache de conteo no leído.
"""
import base64
import hashlib
import secrets
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


def _get_fernet():
    """Retorna instancia Fernet para encriptar/desencriptar tokens.

    Usa FERNET_KEY si está definido (recomendado para producción),
    o deriva de SECRET_KEY como fallback (dev only).
    Rotar SECRET_KEY invalida tokens existentes - usar FERNET_KEY persistente.
    """
    from cryptography.fernet import Fernet
    fernet_key = getattr(settings, 'FERNET_KEY', None)
    if fernet_key:
        key = base64.urlsafe_b64decode(fernet_key)
    else:
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(key)
    return Fernet(key)


def generate_code():
    """Genera código alfanumérico de 6 caracteres para vinculación profesor-estudiante."""
    return secrets.token_hex(3).upper()


class User(AbstractUser):
    """Usuario del sistema con rol asignado y sistema de vinculación.

    Roles: STUDENT, TEACHER, STAFF, PROGRAMMER.
    Los profesores generan un código que los estudiantes usan para vincularse.
    El token de GitHub se encripta con Fernet antes de guardarse en DB.
    """
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Estudiante'
        TEACHER = 'TEACHER', 'Profesor'
        STAFF = 'STAFF', 'Personal'
        PROGRAMMER = 'PROGRAMMER', 'Programador'

    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT, db_index=True)
    code = models.CharField(max_length=6, unique=True, blank=True, null=True)
    linked_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_students')
    github_username = models.CharField(max_length=100, blank=True, null=True)
    github_token = models.TextField(blank=True, null=True)

    # Gamificación
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    badges = models.JSONField(default=list, blank=True)  # Lista de badges ganados

    def set_github_token(self, raw_token):
        """Encripta y guarda el token de GitHub del usuario."""
        if raw_token:
            self.github_token = _get_fernet().encrypt(raw_token.encode()).decode()
        else:
            self.github_token = None

    def get_github_token(self):
        """Desencripta y retorna el token de GitHub, o None si no existe."""
        if not self.github_token:
            return None
        try:
            return _get_fernet().decrypt(self.github_token.encode()).decode()
        except Exception:
            return None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role']

    def save(self, *args, **kwargs):
        """Genera código de vinculación automáticamente para profesores/personal/programadores/admin."""
        if not self.code and self.role != self.Role.STUDENT:
            self.code = generate_code()
            while User.objects.filter(code=self.code).exists():
                self.code = generate_code()
        super().save(*args, **kwargs)

    def unread_notifications_count(self):
        """Retorna cantidad de notificaciones no leídas (con cache de 2 min)."""
        from apps.accounts.cache import get_unread_count
        return get_unread_count(self)

    def add_xp(self, amount, source=''):
        """Añade XP y verifica subida de nivel (cada 25 XP = 1 nivel)."""
        self.xp += amount
        new_level = (self.xp // 25) + 1
        leveled_up = new_level > self.level
        self.level = new_level
        self.save(update_fields=['xp', 'level'])
        return leveled_up

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        # Avatar por defecto basado en iniciales
        return f"https://ui-avatars.com/api/?name={self.get_full_name() or self.email}&background=random&color=fff&size=128"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email', 'role'], name='unique_email_role'),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_role_display()})"


class Notification(models.Model):
    """Notificación del sistema enviada a un usuario.

    Se usa para alertas de tareas, bienvenida, deadlines, y hábitos.
    El conteo de no leídas se cachea y se invalida al crear/marcar como leída.
    meta_key permite tracking idempotente (evita notificaciones duplicadas).
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    meta_key = models.CharField(max_length=100, blank=True, default='', db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read'], name='idx_notif_user_read'),
            models.Index(fields=['user', 'meta_key'], name='idx_notif_user_meta'),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.message[:50]}"


class UserActivity(models.Model):
    """Registro de actividad diaria del usuario para streaks.

    Se crea/actualiza automáticamente cuando el usuario realiza acciones:
    - Completar una tarea
    - Recibir un tip
    - Completar un quiz
    - Login diario
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='activities')
    date = models.DateField(db_index=True)
    tasks_completed = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)
    quizzes_completed = models.PositiveIntegerField(default=0)
    tips_received = models.PositiveIntegerField(default=0)
    login_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.date}"

    @classmethod
    def record_activity(cls, user, activity_type='login'):
        """Registra una actividad y retorna la racha actual."""
        today = timezone.now().date()
        activity, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={f'{activity_type}_count': 1 if activity_type == 'login' else 0}
        )

        if not created:
            if activity_type == 'login':
                activity.login_count += 1
            elif activity_type == 'task':
                activity.tasks_completed += 1
            elif activity_type == 'quiz':
                activity.quizzes_completed += 1
            elif activity_type == 'tip':
                activity.tips_received += 1
            activity.save()

        return cls.get_streak(user)

    @classmethod
    def get_streak(cls, user):
        """Calcula la racha actual de días consecutivos de actividad."""
        today = timezone.now().date()
        streak = 0
        check_date = today

        while True:
            if cls.objects.filter(user=user, date=check_date).exists():
                streak += 1
                check_date -= timezone.timedelta(days=1)
            else:
                break

        return streak

    @classmethod
    def get_best_streak(cls, user):
        """Retorna la mejor racha histórica (aproximación)."""
        from django.db.models import Max
        # Simple: contar días con actividad en los últimos 365 días
        year_ago = timezone.now().date() - timezone.timedelta(days=365)
        active_days = cls.objects.filter(
            user=user, date__gte=year_ago
        ).values_list('date', flat=True).order_by('-date')

        if not active_days:
            return 0

        best = 0
        current = 0
        prev_date = None

        for day in active_days:
            if prev_date and (prev_date - day).days == 1:
                current += 1
            else:
                current = 1
            best = max(best, current)
            prev_date = day

        return best