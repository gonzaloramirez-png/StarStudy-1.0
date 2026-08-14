"""Tests de configuración de perfil: contraseña, datos y preferencias de notificaciones."""
import json
from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Notification, NotificationPreferences
from apps.accounts.tests import make_user
from apps.habits.models import Habit
from apps.tasks.models import Task
from apps.tasks.services import send_task_reminders


class NotificationPreferencesModelTests(TestCase):
    def setUp(self):
        self.user = make_user(email='prefs@starstudy.local', role='STUDENT')

    def test_defaults_son_optin(self):
        prefs, created = NotificationPreferences.objects.get_or_create(user=self.user)
        self.assertTrue(created)
        self.assertTrue(prefs.email_deadlines)
        self.assertTrue(prefs.in_app)
        self.assertTrue(prefs.push)

    def test_get_or_create_no_duplica(self):
        NotificationPreferences.objects.get_or_create(user=self.user)
        NotificationPreferences.objects.get_or_create(user=self.user)
        self.assertEqual(NotificationPreferences.objects.filter(user=self.user).count(), 1)


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = make_user(email='clave@starstudy.local', role='STUDENT', password='ViejaClave123')

    def test_cambio_de_contraseña_exitoso(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('password_change'), {
            'old_password': 'ViejaClave123',
            'new_password1': 'NuevaClave456',
            'new_password2': 'NuevaClave456',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NuevaClave456'))
        self.assertFalse(self.user.check_password('ViejaClave123'))

    def test_cambio_con_contraseña_actual_incorrecta(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('password_change'), {
            'old_password': 'incorrecta',
            'new_password1': 'NuevaClave456',
            'new_password2': 'NuevaClave456',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ViejaClave123'))

    def test_requiere_login(self):
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


class ProfileEditTests(TestCase):
    def setUp(self):
        self.user = make_user(email='datos@starstudy.local', role='TEACHER')

    def test_editar_nombre_y_apellido(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile_edit'), {
            'first_name': 'Juan',
            'last_name': 'Pérez',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Juan')
        self.assertEqual(self.user.last_name, 'Pérez')

    def test_get_no_modifica(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile_edit'))
        self.assertRedirects(response, reverse('profile'))

    def test_requiere_login(self):
        response = self.client.post(reverse('profile_edit'), {'first_name': 'X'})
        self.assertEqual(response.status_code, 302)


class PreferencesViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email='prefview@starstudy.local', role='STUDENT')

    def test_guardar_preferencias(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('notification_preferences'), {
            'email_deadlines': False,
            'in_app': True,
            'push': False,
        })
        self.assertRedirects(response, reverse('profile'))
        prefs = NotificationPreferences.objects.get(user=self.user)
        self.assertFalse(prefs.email_deadlines)
        self.assertTrue(prefs.in_app)
        self.assertFalse(prefs.push)

    def test_perfil_muestra_configuracion(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Configuración')
        self.assertContains(response, 'Cambiar contraseña')
        self.assertContains(response, 'Preferencias de notificaciones')


class PreferencesWiringTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='wprof@starstudy.local', role='TEACHER')
        self.student = make_user(email='wstu@starstudy.local', role='STUDENT')
        Notification.objects.all().delete()

    def make_task_venciendo(self, assigned_to=None):
        return Task.objects.create(
            title='Tarea que vence',
            importance=Task.Importance.MEDIUM,
            deadline=timezone.now() + timedelta(hours=6),
            assigned_by=self.teacher,
            assigned_to=assigned_to or self.student,
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_respeta_preferencia(self):
        NotificationPreferences.objects.create(user=self.student, email_deadlines=False)
        self.make_task_venciendo()
        sent = send_task_reminders()
        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_envia_sin_preferencia_creada(self):
        self.make_task_venciendo()
        sent = send_task_reminders()
        self.assertEqual(sent, 1)
        self.assertEqual(mail.outbox[0].to, [self.student.email])

    def test_push_status_respeta_preferencia(self):
        NotificationPreferences.objects.create(user=self.student, push=False)
        self.client.force_login(self.student)
        response = self.client.get(reverse('push_status'))
        data = json.loads(response.content)
        self.assertFalse(data['push_enabled'])
        self.assertEqual(data['urgent'], [])
        self.assertEqual(data['habits'], [])

    def test_push_status_activo_por_defecto(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('push_status'))
        data = json.loads(response.content)
        self.assertTrue(data['push_enabled'])

    def test_scheduler_deadline_respeta_preferencia(self):
        from apps.schedule.scheduler import check_task_deadlines
        NotificationPreferences.objects.create(user=self.teacher, in_app=False)
        Task.objects.create(
            title='Vence ahora',
            importance=Task.Importance.HIGH,
            deadline=timezone.now() - timedelta(minutes=1),
            assigned_by=self.teacher,
            assigned_to=self.student,
        )
        check_task_deadlines()
        self.assertEqual(Notification.objects.filter(user=self.teacher).count(), 0)

    def test_scheduler_deadline_envia_por_defecto(self):
        from apps.schedule.scheduler import check_task_deadlines
        Task.objects.create(
            title='Vence ahora',
            importance=Task.Importance.HIGH,
            deadline=timezone.now() - timedelta(minutes=1),
            assigned_by=self.teacher,
            assigned_to=self.student,
        )
        check_task_deadlines()
        self.assertTrue(Notification.objects.filter(user=self.teacher).exists())

    def test_scheduler_habit_respeta_preferencia(self):
        from apps.schedule.scheduler import check_habit_notifications
        staff = make_user(email='wstaff@starstudy.local', role='STAFF')
        Notification.objects.create(user=staff, message='limpiar')
        Notification.objects.filter(user=staff).delete()
        NotificationPreferences.objects.create(user=staff, in_app=False)
        Habit.objects.create(
            user=staff,
            title='Leer',
            start_time=timezone.now().time(),
            end_time=timezone.localtime().now().time(),
        )
        check_habit_notifications()
        self.assertEqual(Notification.objects.filter(user=staff).count(), 0)

    def test_scheduler_habit_envia_por_defecto(self):
        from apps.schedule.scheduler import check_habit_notifications
        staff = make_user(email='wstaff2@starstudy.local', role='STAFF')
        Habit.objects.create(
            user=staff,
            title='Leer',
            start_time=timezone.now().time(),
            end_time=timezone.localtime().now().time(),
        )
        check_habit_notifications()
        self.assertTrue(Notification.objects.filter(user=staff).exists())
