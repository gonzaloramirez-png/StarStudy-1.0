"""Tests de hábitos: CRUD, completados y servicios."""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.accounts.tests import make_user
from apps.habits.models import Habit, HabitCompletion
from apps.habits.services import toggle_habit, create_habit, delete_habit


class HabitModelTests(TestCase):
    def setUp(self):
        self.user = make_user(email='hab@h.local', role='STAFF')

    def test_habit_str(self):
        habit = Habit.objects.create(user=self.user, title='Leer', start_time='07:00', end_time='08:00')
        self.assertIn('Leer', str(habit))

    def test_completed_today_false(self):
        habit = Habit.objects.create(user=self.user, title='Leer')
        self.assertFalse(habit.completed_today())

    def test_completed_today_true(self):
        habit = Habit.objects.create(user=self.user, title='Leer')
        HabitCompletion.objects.create(habit=habit, date=timezone.localdate())
        self.assertTrue(habit.completed_today())

    def test_total_completions(self):
        habit = Habit.objects.create(user=self.user, title='Leer')
        HabitCompletion.objects.create(habit=habit, date=timezone.localdate())
        self.assertEqual(habit.total_completions(), 1)


class HabitServiceTests(TestCase):
    def setUp(self):
        self.user = make_user(email='hab-s@h.local', role='STAFF')

    def test_toggle_habit_creates(self):
        habit = Habit.objects.create(user=self.user, title='Meditar')
        created, habit = toggle_habit(habit)
        self.assertTrue(created)
        self.assertTrue(HabitCompletion.objects.filter(habit=habit).exists())

    def test_toggle_habit_removes(self):
        habit = Habit.objects.create(user=self.user, title='Meditar')
        HabitCompletion.objects.create(habit=habit, date=timezone.localdate())
        created, habit = toggle_habit(habit)
        self.assertFalse(created)

    def test_create_habit(self):
        habit = create_habit(self.user, 'Yoga', '07:00', '08:00')
        self.assertIsNotNone(habit.pk)
        self.assertEqual(habit.title, 'Yoga')

    def test_delete_habit(self):
        habit = Habit.objects.create(user=self.user, title='Borrar')
        title = delete_habit(habit)
        self.assertEqual(title, 'Borrar')
        self.assertFalse(Habit.objects.filter(pk=habit.pk).exists())


class HabitViewTests(TestCase):
    def setUp(self):
        self.user = make_user(email='hab-v@h.local', role='STAFF')
        self.client.force_login(self.user)

    def test_habit_list(self):
        response = self.client.get(reverse('habito_list'))
        self.assertEqual(response.status_code, 200)

    def test_habit_create_get(self):
        response = self.client.get(reverse('habito_create'))
        self.assertEqual(response.status_code, 200)
