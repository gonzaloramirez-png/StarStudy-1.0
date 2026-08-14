"""Tests de backends, decorators y levels."""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import authenticate
from apps.accounts.tests import make_user
from apps.accounts.backends import EmailRoleBackend
from apps.accounts.levels import compute_level_and_xp


class EmailRoleBackendTests(TestCase):
    def setUp(self):
        self.user = make_user(email='bk@test.local', role='STUDENT')
        self.backend = EmailRoleBackend()

    def test_authenticate_with_role(self):
        result = authenticate(username='bk@test.local', password='claveSegura123', role='STUDENT')
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.user.pk)

    def test_authenticate_without_role(self):
        result = authenticate(username='bk@test.local', password='claveSegura123')
        self.assertIsNotNone(result)

    def test_authenticate_wrong_password(self):
        result = authenticate(username='bk@test.local', password='mala', role='STUDENT')
        self.assertIsNone(result)

    def test_authenticate_nonexistent(self):
        result = authenticate(username='noexiste@test.local', password='x', role='STUDENT')
        self.assertIsNone(result)

    def test_authenticate_none_credentials(self):
        result = authenticate(username=None, password=None)
        self.assertIsNone(result)

    def test_get_user_exists(self):
        result = self.backend.get_user(self.user.pk)
        self.assertIsNotNone(result)

    def test_get_user_not_exists(self):
        result = self.backend.get_user(99999)
        self.assertIsNone(result)


class LevelsTests(TestCase):
    def test_boundary_values(self):
        level, xp, pct, nxt, needed = compute_level_and_xp(0)
        self.assertEqual(level, 1)
        self.assertEqual(xp, 0)
        self.assertEqual(needed, 5)

    def test_exact_level(self):
        level, xp, _, _, needed = compute_level_and_xp(10)
        self.assertEqual(level, 3)
        self.assertEqual(xp, 0)
        self.assertEqual(needed, 5)

    def test_almost_next(self):
        level, xp, _, _, needed = compute_level_and_xp(9)
        self.assertEqual(level, 2)
        self.assertEqual(xp, 4)
        self.assertEqual(needed, 1)


class DecoratorTests(TestCase):
    def setUp(self):
        self.student = make_user(email='dec-s@t.local', role='STUDENT')
        self.teacher = make_user(email='dec-t@t.local', role='TEACHER')

    def test_role_required_wrong_role(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 302)

    def test_role_required_correct_role(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)
