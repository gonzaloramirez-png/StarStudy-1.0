"""Tests de accounts views: auth, home, profile, push."""
from django.test import TestCase, override_settings
from django.urls import reverse
from apps.accounts.tests import make_user
from apps.accounts.models import User, Notification, NotificationPreferences


class AuthViewTests(TestCase):
    def test_register_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_post(self):
        response = self.client.post(reverse('register'), {
            'email': 'nuevo@test.local',
            'role': 'STUDENT',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'password1': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_join_valid_code(self):
        teacher = make_user(email='join-profe@t.local', role='TEACHER')
        response = self.client.get(reverse('join', args=[teacher.code]))
        self.assertEqual(response.status_code, 302)

    def test_join_invalid_code(self):
        response = self.client.get(reverse('join', args=['XXXXXX']))
        self.assertEqual(response.status_code, 302)

    def test_dismiss_tutorial(self):
        user = make_user(email='dismiss@t.local', role='STUDENT')
        self.client.force_login(user)
        response = self.client.post(reverse('dismiss_tutorial'))
        self.assertIn(response.status_code, [200, 302])


class HomeViewTests(TestCase):
    def setUp(self):
        self.student = make_user(email='home-s@t.local', role='STUDENT')
        self.teacher = make_user(email='home-t@t.local', role='TEACHER')

    def test_home_student(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_teacher(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_staff(self):
        staff = make_user(email='home-staff@t.local', role='STAFF')
        self.client.force_login(staff)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_programmer(self):
        prog = make_user(email='home-prog@t.local', role='PROGRAMMER')
        self.client.force_login(prog)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email='prof-v@t.local', role='STUDENT')
        self.client.force_login(self.user)

    def test_profile_get(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)


class PushViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email='push@t.local', role='STUDENT')
        self.client.force_login(self.user)

    def test_push_status(self):
        response = self.client.get(reverse('push_status'))
        self.assertEqual(response.status_code, 200)

    def test_service_worker(self):
        response = self.client.get(reverse('service_worker'))
        self.assertEqual(response.status_code, 200)


class NotificationViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email='notif@t.local', role='STUDENT')
        self.client.force_login(self.user)

    def test_notification_list(self):
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 200)

    def test_notification_read(self):
        notif = Notification.objects.create(user=self.user, message='Test', link='/tasks/')
        response = self.client.post(reverse('notification_read', args=[notif.pk]))
        self.assertIn(response.status_code, [200, 302])
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
