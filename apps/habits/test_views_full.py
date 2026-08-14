"""Tests de habit views: CRUD completo."""
from django.test import TestCase
from django.urls import reverse
from apps.accounts.tests import make_user
from apps.habits.models import Habit


class HabitViewFullTests(TestCase):
    def setUp(self):
        self.user = make_user(email='hab-full@h.local', role='STAFF')
        self.client.force_login(self.user)

    def test_habit_list(self):
        response = self.client.get(reverse('habito_list'))
        self.assertEqual(response.status_code, 200)

    def test_habit_create_get(self):
        response = self.client.get(reverse('habito_create'))
        self.assertEqual(response.status_code, 200)

    def test_habit_create_post(self):
        response = self.client.post(reverse('habito_create'), {
            'title': 'Yoga',
            'start_time': '07:00',
            'end_time': '08:00',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_habit_delete(self):
        habit = Habit.objects.create(user=self.user, title='Borrar')
        response = self.client.post(reverse('habito_delete', args=[habit.pk]))
        self.assertIn(response.status_code, [200, 302])

    def test_habit_toggle(self):
        habit = Habit.objects.create(user=self.user, title='Toggle')
        response = self.client.post(reverse('habito_toggle', args=[habit.pk]))
        self.assertIn(response.status_code, [200, 302])
