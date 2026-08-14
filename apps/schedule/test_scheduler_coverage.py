"""Tests de scheduler: check_task_deadlines, check_habit_notifications."""
from datetime import timedelta, time as dt_time
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from apps.accounts.tests import make_user
from apps.accounts.models import Notification, NotificationPreferences
from apps.tasks.models import Task
from apps.habits.models import Habit


def _fake_now():
    return timezone.datetime(2026, 8, 10, 10, 0, 0, tzinfo=timezone.utc)


class SchedulerTaskDeadlineTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='sched-t@t.local', role='TEACHER')
        self.student = make_user(email='sched-s@t.local', role='STUDENT')
        Notification.objects.all().delete()

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_creates_notification(self):
        from apps.schedule.scheduler import check_task_deadlines
        task = Task.objects.create(
            title='Vence pronto', importance='HIGH',
            deadline=_fake_now() - timedelta(minutes=1),
            assigned_by=self.teacher, assigned_to=self.student,
        )
        check_task_deadlines()
        self.assertTrue(Notification.objects.filter(user=self.teacher, meta_key=f'deadline_{task.pk}_{task.deadline.date()}').exists())

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_respects_in_app_off(self):
        from apps.schedule.scheduler import check_task_deadlines
        NotificationPreferences.objects.create(user=self.teacher, in_app=False)
        Task.objects.create(
            title='Vence', importance='HIGH',
            deadline=_fake_now() - timedelta(minutes=1),
            assigned_by=self.teacher, assigned_to=self.student,
        )
        check_task_deadlines()
        self.assertEqual(Notification.objects.filter(user=self.teacher).count(), 0)

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_skips_completed(self):
        from apps.schedule.scheduler import check_task_deadlines
        Task.objects.create(
            title='Ya', importance='HIGH', deadline=_fake_now() - timedelta(minutes=1),
            assigned_by=self.teacher, assigned_to=self.student, is_completed=True,
        )
        check_task_deadlines()
        self.assertFalse(Notification.objects.filter(user=self.teacher).exists())


class SchedulerHabitTests(TestCase):
    def setUp(self):
        self.staff = make_user(email='sched-staff@t.local', role='STAFF')
        Notification.objects.all().delete()

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_creates_notification(self):
        from apps.schedule.scheduler import check_habit_notifications
        Habit.objects.create(user=self.staff, title='Leer', start_time=dt_time(10, 0), end_time=dt_time(11, 0))
        check_habit_notifications()
        self.assertTrue(Notification.objects.filter(user=self.staff, meta_key__contains='habit').exists())

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_respects_in_app_off(self):
        from apps.schedule.scheduler import check_habit_notifications
        NotificationPreferences.objects.create(user=self.staff, in_app=False)
        Habit.objects.create(user=self.staff, title='Leer', start_time=dt_time(10, 0), end_time=dt_time(11, 0))
        check_habit_notifications()
        self.assertFalse(Notification.objects.filter(user=self.staff).exists())

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_skips_zero_time(self):
        from apps.schedule.scheduler import check_habit_notifications
        Habit.objects.create(user=self.staff, title='Sin horario', start_time=dt_time(0, 0), end_time=dt_time(0, 0))
        check_habit_notifications()
        self.assertFalse(Notification.objects.filter(user=self.staff).exists())
