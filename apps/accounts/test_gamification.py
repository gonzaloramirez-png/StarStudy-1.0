"""Tests de gamificación: rachas y desbloqueo de badges."""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Badge, UserBadge
from apps.accounts.gamification import check_badges, current_streak, get_badges
from apps.accounts.tests import make_user
from apps.habits.models import Habit, HabitCompletion
from apps.tasks.models import Task
from apps.tasks.services import complete_task


def badge_count(user):
    return UserBadge.objects.filter(user=user).count()


def make_completed_task(user, importance=Task.Importance.MEDIUM):
    return Task.objects.create(
        title='Tarea de prueba',
        importance=importance,
        deadline=timezone.now() + timedelta(days=1),
        assigned_by=user,
        assigned_to=user,
        is_personal=True,
        is_completed=True,
    )


def complete_n_tasks(user, n):
    for _ in range(n):
        complete_task(make_completed_task(user), user)


class StreakTests(TestCase):
    def setUp(self):
        self.user = make_user(email='racha@starstudy.local', role='STAFF')
        self.habit = Habit.objects.create(
            user=self.user, title='Leer', start_time='20:00', end_time='21:00')

    def test_dias_consecutivos(self):
        today = timezone.localdate()
        for i in range(3):
            HabitCompletion.objects.create(
                habit=self.habit, date=today - timedelta(days=i))
        self.assertEqual(current_streak(self.user), 3)

    def test_hoy_sin_completar_no_rompe_la_racha(self):
        today = timezone.localdate()
        HabitCompletion.objects.create(habit=self.habit, date=today - timedelta(days=1))
        HabitCompletion.objects.create(habit=self.habit, date=today - timedelta(days=2))
        self.assertEqual(current_streak(self.user), 2)

    def test_hueco_rompe_la_racha(self):
        today = timezone.localdate()
        HabitCompletion.objects.create(habit=self.habit, date=today)
        HabitCompletion.objects.create(habit=self.habit, date=today - timedelta(days=2))
        self.assertEqual(current_streak(self.user), 1)

    def test_sin_habitos_racha_cero(self):
        user = make_user(email='sinracha@starstudy.local', role='STUDENT')
        self.assertEqual(current_streak(user), 0)


class BadgeTests(TestCase):
    def setUp(self):
        self.user = make_user(email='logros@starstudy.local', role='STAFF')
        self.habit = Habit.objects.create(
            user=self.user, title='Leer', start_time='20:00', end_time='21:00')

    def test_primera_tarea_desbloquea_primer_paso(self):
        unlocked = check_badges(self.user, completed_count=1, critical_count=0)
        codes = {b.code for b in unlocked}
        self.assertIn('first_task', codes)
        self.assertTrue(Badge.objects.filter(code='first_task', user_badges__user=self.user).exists())

    def test_check_badges_es_idempotente(self):
        make_completed_task(self.user)
        check_badges(self.user)
        self.assertEqual(badge_count(self.user), 1)
        self.assertEqual(check_badges(self.user), [])

    def test_una_critica_desbloquea_bajo_presion(self):
        make_completed_task(self.user, importance=Task.Importance.CRITICAL)
        check_badges(self.user)
        self.assertTrue(
            Badge.objects.filter(code='critical_task', user_badges__user=self.user).exists())

    def test_racha_desbloquea_badges_de_racha(self):
        today = timezone.localdate()
        for i in range(3):
            HabitCompletion.objects.create(
                habit=self.habit, date=today - timedelta(days=i))
        check_badges(self.user)
        self.assertTrue(
            Badge.objects.filter(code='streak_3', user_badges__user=self.user).exists())
        self.assertFalse(
            Badge.objects.filter(code='streak_7', user_badges__user=self.user).exists())

    def test_dia_perfecto_requiere_todos_los_habitos(self):
        otro = Habit.objects.create(
            user=self.user, title='Ejercicio', start_time='08:00', end_time='09:00')
        HabitCompletion.objects.create(habit=self.habit, date=timezone.localdate())
        check_badges(self.user)
        self.assertFalse(
            Badge.objects.filter(code='daily_full', user_badges__user=self.user).exists())
        HabitCompletion.objects.create(habit=otro, date=timezone.localdate())
        check_badges(self.user)
        self.assertTrue(
            Badge.objects.filter(code='daily_full', user_badges__user=self.user).exists())

    def test_diez_tareas_desbloquean_doble_digito(self):
        for _ in range(10):
            make_completed_task(self.user)
        check_badges(self.user)
        self.assertTrue(
            Badge.objects.filter(code='ten_tasks', user_badges__user=self.user).exists())

    def test_get_badges_separa_desbloqueados_y_bloqueados(self):
        make_completed_task(self.user)
        check_badges(self.user)
        unlocked, locked = get_badges(self.user)
        self.assertTrue(any(b.code == 'first_task' for b in unlocked))
        self.assertTrue(any(b.code == 'fifty_tasks' for b in locked))


class BadgeIntegrationTests(TestCase):
    def test_completar_tarea_via_servicio_desbloquea(self):
        user = make_user(email='integ@starstudy.local', role='STAFF')
        task = Task.objects.create(
            title='Primera',
            importance=Task.Importance.MEDIUM,
            deadline=timezone.now() + timedelta(days=1),
            assigned_by=user,
            assigned_to=user,
            is_personal=True,
        )
        complete_task(task, user)
        self.assertTrue(
            Badge.objects.filter(code='first_task', user_badges__user=user).exists())

    def test_toggle_habit_via_servicio_acumula_racha(self):
        user = make_user(email='hab@starstudy.local', role='STAFF')
        habit = Habit.objects.create(
            user=user, title='Leer', start_time='20:00', end_time='21:00')
        today = timezone.localdate()
        for i in range(1, 3):
            HabitCompletion.objects.create(habit=habit, date=today - timedelta(days=i))
        from apps.habits.services import toggle_habit
        toggle_habit(habit)
        self.assertEqual(current_streak(user), 3)
        self.assertTrue(
            Badge.objects.filter(code='streak_3', user_badges__user=user).exists())

    def test_perfil_muestra_logros_y_racha(self):
        user = make_user(email='perfil@starstudy.local', role='STAFF')
        make_completed_task(user)
        check_badges(user)
        self.client.force_login(user)
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Logros')
        self.assertContains(response, 'Primer paso')
        self.assertContains(response, 'Racha de Misión Principal')
