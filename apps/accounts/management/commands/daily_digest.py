"""Comando para generar digest diario de notificaciones.

Envía un resumen consolidado de actividad del día a cada usuario.
Evita el spam de correos individuales.

Uso:
    python manage.py daily_digest
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from apps.accounts.models import User, Notification
from apps.tasks.models import Task


class Command(BaseCommand):
    help = 'Genera digest diario de notificaciones para todos los usuarios activos'

    def handle(self, *args, **options):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        now = timezone.now()

        users = User.objects.filter(is_active=True).exclude(role='PROGRAMMER')
        sent_count = 0

        for user in users:
            # Tareas que vencen hoy
            due_today = Task.objects.filter(
                assigned_to=user,
                deadline__date=today,
                is_completed=False,
            ).count()

            # Tareas vencidas (urgentes)
            overdue = Task.objects.filter(
                assigned_to=user,
                deadline__date__lt=today,
                is_completed=False,
            ).count()

            # Tareas completadas ayer
            completed_yesterday = Task.objects.filter(
                assigned_to=user,
                is_completed=True,
                completed_at__date=yesterday,
            ).count()

            # XP ganada ayer
            from django.db.models import Sum
            xp_yesterday = Task.objects.filter(
                assigned_to=user,
                is_completed=True,
                completed_at__date=yesterday,
            ).aggregate(total=Sum('score'))['total'] or 0

            # Nuevas tareas asignadas
            new_tasks = Task.objects.filter(
                assigned_to=user,
                created_at__date=yesterday,
            ).count()

            # Solo enviar si hay algo relevante
            if due_today == 0 and overdue == 0 and completed_yesterday == 0 and new_tasks == 0:
                continue

            # Construir mensaje del digest
            parts = []
            if due_today > 0:
                parts.append(f'📅 {due_today} tarea(s) vence(n) hoy')
            if overdue > 0:
                parts.append(f'⚠️ {overdue} tarea(s) vencida(s)')
            if completed_yesterday > 0:
                parts.append(f'✅ Completaste {completed_yesterday} tarea(s) ayer')
            if xp_yesterday > 0:
                parts.append(f'⭐ +{xp_yesterday} XP ganados')
            if new_tasks > 0:
                parts.append(f'📋 {new_tasks} nueva(s) tarea(s) asignada(s)')

            message = ' | '.join(parts)

            # Crear notificación de digest (meta_key para evitar duplicados)
            meta_key = f'daily_digest_{today}'
            exists = Notification.objects.filter(
                user=user,
                meta_key=meta_key,
            ).exists()

            if not exists:
                Notification.objects.create(
                    user=user,
                    message=f'📊 Resumen del día: {message}',
                    link='/tasks/mi-dia/',
                    meta_key=meta_key,
                )
                sent_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Digest diario enviado a {sent_count} usuarios'
        ))
