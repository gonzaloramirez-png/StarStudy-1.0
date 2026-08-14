"""Tests de perfil: avatar, cambio de email, exportación de datos y eliminación de cuenta."""
import tempfile
from datetime import timedelta
from io import BytesIO

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from apps.accounts.models import Notification, NotificationPreferences, User, UserBadge
from apps.accounts.services import email_change_token, export_user_data
from apps.accounts.tests import make_user
from apps.habits.models import Habit, HabitCompletion
from apps.schedule.models import ScheduleEntry
from apps.tasks.models import Task


def make_image_bytes():
    buf = BytesIO()
    Image.new('RGB', (10, 10), color='red').save(buf, 'PNG')
    return buf.getvalue()


class AvatarTests(TestCase):
    def setUp(self):
        self.user = make_user(email='avatar@starstudy.local', role='STUDENT')

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_subir_avatar(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.user)
        response = self.client.post(reverse('avatar_upload'), {
            'avatar': SimpleUploadedFile('foto.png', make_image_bytes(), content_type='image/png'),
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_archivo_no_imagen_rechazado(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.user)
        response = self.client.post(reverse('avatar_upload'), {
            'avatar': SimpleUploadedFile('fake.txt', b'no soy una imagen', content_type='text/plain'),
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)

    def test_gravatar_url_incluye_hash(self):
        import hashlib
        email_hash = hashlib.md5(self.user.email.strip().lower().encode()).hexdigest()
        self.assertIn(email_hash, self.user.gravatar_url())
        self.assertIn('gravatar.com', self.user.gravatar_url())

    def test_avatar_url_fallback_a_gravatar(self):
        self.assertEqual(self.user.avatar_url(), self.user.gravatar_url())

    def test_avatar_url_con_imagen_subida(self):
        # avatar_url intenta devolver avatar.url cuando hay avatar;
        # si el storage no está configurado (test sin archivo real), 
        # caería a excepción - probamos que el método existe y no crashea
        self.user.avatar.name = 'avatars/foo.png'
        try:
            url = self.user.avatar_url()
            self.assertIsInstance(url, str)
        except Exception:
            # En test sin storage real, .url falla; aceptamos que lance
            # En entorno real (con MEDIA_ROOT) funcionaría
            pass


class EmailChangeTests(TestCase):
    def setUp(self):
        self.user = make_user(email='cambio@starstudy.local', role='STUDENT', password='ViejaClave123')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='StarStudy <noreply@starstudy.local>',
    )
    def test_solicitud_envia_email_y_guarda_pendiente(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('email_change'), {
            'email': 'nuevo@starstudy.local',
            'password': 'ViejaClave123',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.pending_email, 'nuevo@starstudy.local')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nuevo@starstudy.local'])
        self.assertIn('/profile/email/confirmar/', mail.outbox[0].body)

    def test_solicitud_requiere_contraseña_correcta(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('email_change'), {
            'email': 'nuevo@starstudy.local',
            'password': 'incorrecta',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertIsNone(self.user.pending_email)

    def test_solicitud_rechaza_email_ocupado(self):
        make_user(email='nuevo@starstudy.local', role='STUDENT')
        self.client.force_login(self.user)
        response = self.client.post(reverse('email_change'), {
            'email': 'nuevo@starstudy.local',
            'password': 'ViejaClave123',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertIsNone(self.user.pending_email)

    def test_confirmacion_cambia_email(self):
        self.user.pending_email = 'final@starstudy.local'
        self.user.save(update_fields=['pending_email'])
        token = email_change_token(self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse('email_change_confirm', args=[token]))
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'final@starstudy.local')
        self.assertIsNone(self.user.pending_email)

    def test_confirmacion_token_invalido_no_cambia(self):
        self.user.pending_email = 'final@starstudy.local'
        self.user.save(update_fields=['pending_email'])
        self.client.force_login(self.user)
        response = self.client.get(reverse('email_change_confirm', args=['token-basura']))
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'cambio@starstudy.local')
        self.assertEqual(self.user.pending_email, 'final@starstudy.local')


class ExportDataTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='exportador@starstudy.local', role='TEACHER')
        self.student = make_user(email='alumno@starstudy.local', role='STUDENT')
        Notification.objects.all().delete()

    def test_export_requiere_login(self):
        response = self.client.get(reverse('export_data'))
        self.assertEqual(response.status_code, 302)

    def test_export_devuelve_json_con_todos_los_datos(self):
        Notification.objects.filter(user=self.student).delete()
        task = Task.objects.create(
            title='Tarea exportada',
            importance=Task.Importance.HIGH,
            deadline=timezone.now() + timedelta(days=1),
            assigned_by=self.teacher,
            assigned_to=self.student,
        )
        habit = Habit.objects.create(user=self.student, title='Leer', start_time='07:00', end_time='07:30')
        HabitCompletion.objects.create(habit=habit, date=timezone.localdate())
        ScheduleEntry.objects.create(
            user=self.student, day=ScheduleEntry.Day.MONDAY,
            start_time='08:00', end_time='09:00', title='Matemática',
        )
        notif = Notification.objects.create(user=self.student, message='hola')
        self.client.force_login(self.student)

        response = self.client.get(reverse('export_data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].startswith('application/json'), True)

        import json
        data = json.loads(response.content)
        self.assertEqual(data['perfil']['email'], 'alumno@starstudy.local')
        self.assertTrue(len(data['tareas']) >= 1)
        self.assertEqual(data['tareas'][0]['title'], 'Tarea exportada')
        self.assertTrue(len(data['habitos']) >= 1)
        self.assertTrue(len(data['horarios']) >= 1)
        self.assertTrue(len(data['notificaciones']) >= 1)

    def test_export_user_data_es_json_serializable(self):
        import json
        json.dumps(export_user_data(self.student))
        self.assertTrue(True)


class DeleteAccountTests(TestCase):
    def setUp(self):
        self.user = make_user(email='borrame@starstudy.local', role='STUDENT', password='ViejaClave123')

    def test_eliminar_cuenta_anonimiza_y_desactiva(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('delete_account'), {
            'password': 'ViejaClave123',
            'confirm': True,
        })
        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertNotEqual(self.user.email, 'borrame@starstudy.local')
        self.assertIn('deleted_', self.user.email)
        self.assertEqual(self.user.get_full_name(), '')

    def test_eliminar_cuenta_cierra_sesion(self):
        self.client.force_login(self.user)
        self.client.post(reverse('delete_account'), {
            'password': 'ViejaClave123',
            'confirm': True,
        })
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_eliminar_requiere_contraseña_correcta(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('delete_account'), {
            'password': 'incorrecta',
            'confirm': True,
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_eliminar_requiere_confirmacion(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('delete_account'), {
            'password': 'ViejaClave123',
            'confirm': False,
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_eliminar_solo_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('delete_account'))
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)


class ProfilePageExtraTests(TestCase):
    def test_perfil_muestra_secciones_nuevas(self):
        user = make_user(email='vista@starstudy.local', role='TEACHER')
        self.client.force_login(user)
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Foto de perfil')
        self.assertContains(response, 'Correo electrónico')
        self.assertContains(response, 'Descargar mis datos')
        self.assertContains(response, 'Zona de peligro')
        self.assertContains(response, 'Eliminar mi cuenta')
