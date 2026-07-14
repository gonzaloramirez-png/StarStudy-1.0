"""Models de accounts: Usuario y Notificaciones.

- User: Extiende AbstractUser con roles (Estudiante, Profesor, Personal, Programador),
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
        """Genera código de vinculación automáticamente para profesores/personal/programadores."""
        if not self.code and self.role != self.Role.STUDENT:
            self.code = generate_code()
            while User.objects.filter(code=self.code).exists():
                self.code = generate_code()
        super().save(*args, **kwargs)

    def unread_notifications_count(self):
        """Retorna cantidad de notificaciones no leídas (con cache de 2 min)."""
        from apps.accounts.cache import get_unread_count
        return get_unread_count(self)

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
