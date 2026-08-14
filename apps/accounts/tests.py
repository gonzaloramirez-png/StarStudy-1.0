"""Tests de accounts: gamificación, login, contraseñas y permisos."""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse
from django.core import mail

from apps.accounts.levels import compute_level_and_xp

User = get_user_model()


def make_user(email='test@starstudy.local', role='STUDENT', password='claveSegura123'):
    return User.objects.create_user(
        username=email.split('@')[0] + '_' + role.lower(),
        email=email,
        password=password,
        role=role,
    )


class LevelAndXpTests(TestCase):
    def test_nivel_1_sin_tareas(self):
        self.assertEqual(compute_level_and_xp(0), (1, 0, 0, 5, 5))

    def test_cinco_tareas_suben_un_nivel(self):
        level, xp, percent, next_xp, needed = compute_level_and_xp(5)
        self.assertEqual(level, 2)
        self.assertEqual(xp, 0)
        self.assertEqual(percent, 0)
        self.assertEqual(needed, 5)

    def test_xp_intermedio(self):
        level, xp, percent, next_xp, needed = compute_level_and_xp(7)
        self.assertEqual(level, 2)
        self.assertEqual(xp, 2)
        self.assertEqual(percent, 40)
        self.assertEqual(needed, 3)

    def test_valores_negativos_o_none(self):
        self.assertEqual(compute_level_and_xp(None)[0], 1)
        self.assertEqual(compute_level_and_xp(-3)[0], 1)


class LoginTests(TestCase):
    def setUp(self):
        self.student = make_user()

    def test_login_con_email(self):
        user = authenticate(username='test@starstudy.local', password='claveSegura123')
        self.assertIsNotNone(user)
        self.assertEqual(user.pk, self.student.pk)

    def test_login_contraseña_incorrecta(self):
        user = authenticate(username='test@starstudy.local', password='incorrecta')
        self.assertIsNone(user)


class PasswordResetTests(TestCase):
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='StarStudy <noreply@starstudy.local>',
    )
    def test_flujo_completo_de_recuperacion(self):
        make_user(email='olvido@starstudy.local', role='TEACHER')
        response = self.client.post(reverse('password_reset'), {
            'email': 'olvido@starstudy.local',
        })
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        # El correo contiene un enlace con token
        self.assertIn('/reset/', body)

    def test_email_inexistente_no_rompe(self):
        response = self.client.post(reverse('password_reset'), {
            'email': 'nadie@starstudy.local',
        })
        self.assertRedirects(response, reverse('password_reset_done'))


class PermissionTests(TestCase):
    def test_estudiante_no_puede_crear_tareas(self):
        student = make_user()
        self.client.force_login(student)
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_estudiante_no_puede_ver_horario_del_curso_sin_vincularse(self):
        student = make_user()
        self.client.force_login(student)
        response = self.client.get(reverse('schedule_student_course'))
        self.assertRedirects(response, reverse('schedule_personal'))

    def test_no_autenticado_redirige_a_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_logout_solo_post(self):
        student = make_user()
        self.client.force_login(student)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.url, reverse('login'))
