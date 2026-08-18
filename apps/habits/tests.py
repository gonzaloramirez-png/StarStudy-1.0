"""Tests de habits: lógica de la Misión Principal, CRUD completo y servicios."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.accounts.tests import make_user
from apps.habits.models import Habit, HabitCompletion
from apps.habits.services import toggle_habit, create_habit, delete_habit

User = get_user_model()


def make_staff(email='staff@starstudy.local'):
    return User.objects.create_user(
        username=email.split('@')[0] + '_staff',
        email=email,
        password='claveSegura123',
        role='STAFF',
    )


class HabitToggleTests(TestCase):
    """Tests de habits: lógica de la Misión Principal."""

    def setUp(self):
        self.staff = make_staff()
        self.habit = Habit.objects.create(
            user=self.staff,
            title='Leer 30 minutos',
            start_time='20:00',
            end_time='20:30',
        )

    def test_completar_habit_sube_nivel(self):
        created, habit = toggle_habit(self.habit)
        self.assertTrue(created)
        self.assertEqual(habit.level, 2)
        self.assertTrue(HabitCompletion.objects.filter(habit=habit).exists())

    def test_no_se_puede_completar_dos_veces_el_mismo_dia(self):
        toggle_habit(self.habit)
        created, habit = toggle_habit(self.habit)
        self.assertFalse(created)
        self.assertEqual(habit.level, 2)

    def test_crear_habit(self):
        response = self.client.force_login(self.staff)
        self.client.post(reverse('habito_create'), {
            'title': 'Meditar',
            'start_time': '07:00',
            'end_time': '07:15',
        })
        self.assertTrue(Habit.objects.filter(title='Meditar').exists())


class HabitPermissionTests(TestCase):
    def test_solo_staff_accede_a_habitos(self):
        from apps.accounts.tests import make_user as make_any_user
        student = make_any_user('alu-hab@starstudy.local', 'STUDENT')
        self.client.force_login(student)
        response = self.client.get(reverse('habito_list'))
        self.assertRedirects(response, reverse('home'))


class HabitHtmxTests(TestCase):
    def setUp(self):
        self.staff = make_staff('staff-hx@starstudy.local')
        self.habit = Habit.objects.create(
            user=self.staff,
            title='Leer 30 minutos',
            start_time='20:00',
            end_time='20:30',
        )

    def test_toggle_htmx_actualiza_fila(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('habito_toggle', args=[self.habit.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hecho')
        self.assertIn('toast:', response['HX-Trigger'])
        self.assertIn('"type": "success"', response['HX-Trigger'])

    def test_toggle_repetido_htmx_devuelve_toast_error(self):
        toggle_habit(self.habit)
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('habito_toggle', args=[self.habit.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('"type": "error"', response['HX-Trigger'])

    def test_delete_htmx_devuelve_cuerpo_vacio_y_toast(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('habito_delete', args=[self.habit.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertIn('toast:', response['HX-Trigger'])
        self.assertFalse(Habit.objects.filter(pk=self.habit.pk).exists())


class HabitViewFullTests(TestCase):
    """Tests de habit views: CRUD completo."""

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


class HabitModelTests(TestCase):
    """Tests de hábitos: CRUD, completados y servicios."""

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
