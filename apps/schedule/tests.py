"""Tests de schedule: validación del formulario, permisos, vistas, utils, servicios y scheduler."""
from datetime import time, timedelta, time as dt_time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Notification, NotificationPreferences
from apps.habits.models import Habit
from apps.schedule.forms import ScheduleEntryForm
from apps.schedule.models import ScheduleEntry
from apps.schedule.scheduler import check_habit_notifications, check_task_deadlines
from apps.schedule.services import (
    get_schedule_context, add_schedule_entry, delete_schedule_entry,
)
from apps.schedule.utils import build_schedule_table
from apps.tasks.models import Task

User = get_user_model()


def make_user(email, role):
    return User.objects.create_user(
        username=email.split('@')[0] + '_' + role.lower(),
        email=email,
        password='claveSegura123',
        role=role,
    )


def _fake_now():
    return timezone.datetime(2026, 8, 10, 10, 0, 0, tzinfo=timezone.utc)


class ScheduleFormTests(TestCase):
    def setUp(self):
        self.teacher = make_user('profe-h@starstudy.local', 'TEACHER')

    def test_hora_fin_debe_ser_posterior(self):
        form = ScheduleEntryForm(
            data={
                'day': 'MON',
                'start_time': '18:00',
                'end_time': '17:00',
                'title': 'Matemáticas',
                'entry_type': 'SUBJECT',
            },
            user=self.teacher,
        )
        self.assertFalse(form.is_valid())

    def test_no_permite_superposicion(self):
        ScheduleEntry.objects.create(
            user=self.teacher, day='MON',
            start_time='10:00', end_time='11:00',
            title='Clase A', entry_type='SUBJECT',
        )
        form = ScheduleEntryForm(
            data={
                'day': 'MON',
                'start_time': '10:30',
                'end_time': '11:30',
                'title': 'Clase B',
                'entry_type': 'SUBJECT',
            },
            user=self.teacher,
        )
        self.assertFalse(form.is_valid())


class SchedulePermissionTests(TestCase):
    def test_solo_profesor_accede_al_horario_del_curso(self):
        student = make_user('alu-h@starstudy.local', 'STUDENT')
        self.client.force_login(student)
        response = self.client.get(reverse('schedule_course'))
        self.assertRedirects(response, reverse('home'))

    def test_estudiante_ve_horario_del_curso_de_su_profesor(self):
        teacher = make_user('profe-vin@starstudy.local', 'TEACHER')
        ScheduleEntry.objects.create(
            user=teacher, day='WED', schedule_type='COURSE',
            start_time='08:00', end_time='09:00',
            title='Programación', entry_type='SUBJECT',
        )
        student = make_user('alu-vin@starstudy.local', 'STUDENT')
        student.linked_to = teacher
        student.save(update_fields=['linked_to'])

        self.client.force_login(student)
        response = self.client.get(reverse('schedule_student_course'))
        self.assertEqual(response.status_code, 200)
        entries = response.context['all_entries']
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, 'Programación')


class ScheduleViewTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='sch-views@t.local', role='TEACHER')
        self.student = make_user(email='sch-views-s@t.local', role='STUDENT')

    def test_schedule_personal(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('schedule_personal'))
        self.assertEqual(response.status_code, 200)

    def test_schedule_personal_post_add(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('schedule_personal'), {
            'add': True,
            'day': 'MON',
            'start_time': '08:00',
            'end_time': '09:00',
            'title': 'Matemática',
            'entry_type': 'SUBJECT',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_schedule_course(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('schedule_course'))
        self.assertEqual(response.status_code, 200)

    def test_schedule_student_course_no_linked(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('schedule_student_course'))
        self.assertEqual(response.status_code, 302)

    def test_schedule_student_course_linked(self):
        teacher2 = make_user(email='sch-teacher2@t.local', role='TEACHER')
        self.student.linked_to = teacher2
        self.student.save(update_fields=['linked_to'])
        self.client.force_login(self.student)
        response = self.client.get(reverse('schedule_student_course'))
        self.assertEqual(response.status_code, 200)

    def test_schedule_personal_delete(self):
        self.client.force_login(self.teacher)
        entry = ScheduleEntry.objects.create(user=self.teacher, day='MON', start_time='08:00', end_time='09:00', title='Borrar', schedule_type='PERSONAL')
        response = self.client.post(reverse('schedule_personal'), {'delete_id': entry.pk})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ScheduleEntry.objects.filter(pk=entry.pk).exists())


class BuildScheduleTableTests(TestCase):
    def test_empty_entries(self):
        rows = build_schedule_table([], ['MON', 'TUE'])
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0][0], '08:00')

    def test_with_entries(self):
        entry = type('E', (), {'day': 'MON', 'start_time': time(8, 0)})()
        rows = build_schedule_table([entry], ['MON'])
        self.assertTrue(len(rows) > 0)
        self.assertEqual(rows[0][0], '08:00')


class ScheduleServiceTests(TestCase):
    def setUp(self):
        self.user = make_user(email='sch-s@s.local', role='TEACHER')

    def test_get_schedule_context_personal(self):
        ctx = get_schedule_context(self.user, ScheduleEntry.ScheduleType.PERSONAL, 'Personal')
        self.assertIn('rows', ctx)
        self.assertIn('days', ctx)
        self.assertFalse(ctx['readonly'])

    def test_get_schedule_context_with_entries(self):
        ScheduleEntry.objects.create(user=self.user, day='MON', start_time=time(8, 0), end_time=time(9, 0), title='Mat', schedule_type=ScheduleEntry.ScheduleType.PERSONAL)
        ctx = get_schedule_context(self.user, ScheduleEntry.ScheduleType.PERSONAL, 'Personal')
        self.assertTrue(len(ctx['all_entries']) > 0)

    def test_add_schedule_entry(self):
        form_data = {'day': 'TUE', 'start_time': '10:00', 'end_time': '11:00', 'title': 'Historia', 'entry_type': 'SUBJECT'}
        form = ScheduleEntryForm(data=form_data)
        self.assertTrue(form.is_valid())
        entry = add_schedule_entry(self.user, form, ScheduleEntry.ScheduleType.PERSONAL)
        self.assertIsNotNone(entry.pk)
        self.assertEqual(entry.user, self.user)

    def test_delete_schedule_entry(self):
        entry = ScheduleEntry.objects.create(user=self.user, day='WED', start_time=time(10, 0), end_time=time(11, 0), title='Borrar')
        delete_schedule_entry(entry.pk, self.user)
        self.assertFalse(ScheduleEntry.objects.filter(pk=entry.pk).exists())

    def test_delete_nonexistent_entry(self):
        delete_schedule_entry(99999, self.user)

    def test_group_entries_by_day(self):
        ScheduleEntry.objects.create(user=self.user, day='MON', start_time=time(8, 0), end_time=time(9, 0), title='A')
        ScheduleEntry.objects.create(user=self.user, day='FRI', start_time=time(10, 0), end_time=time(11, 0), title='B')
        entries = list(ScheduleEntry.objects.all())
        groups = _group_entries_by_day(entries)
        self.assertEqual(len(groups), 5)

    def test_get_schedule_context_readonly_course_no_linked(self):
        student = make_user(email='readonly@s.local', role='STUDENT')
        ctx = get_schedule_context(student, ScheduleEntry.ScheduleType.COURSE, 'Clase', readonly=True)
        self.assertIsNotNone(ctx)


class UtilsTests(TestCase):
    def test_build_schedule_table_empty(self):
        rows = build_schedule_table([], ['MON', 'TUE'])
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0][0], '08:00')

    def test_build_schedule_table_with_entries(self):
        entry = type('Entry', (), {'day': 'MON', 'start_time': time(8, 0)})()
        rows = build_schedule_table([entry], ['MON'])
        self.assertTrue(len(rows) > 0)


class SchedulerTaskDeadlineTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='sched-t@t.local', role='TEACHER')
        self.student = make_user(email='sched-s@t.local', role='STUDENT')
        Notification.objects.all().delete()

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_creates_notification(self):
        task = Task.objects.create(
            title='Vence pronto', importance='HIGH',
            deadline=_fake_now() - timedelta(minutes=1),
            assigned_by=self.teacher, assigned_to=self.student,
        )
        check_task_deadlines()
        self.assertTrue(Notification.objects.filter(user=self.teacher, meta_key=f'deadline_{task.pk}_{task.deadline.date()}').exists())

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_respects_in_app_off(self):
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
        Habit.objects.create(user=self.staff, title='Leer', start_time=dt_time(10, 0), end_time=dt_time(11, 0))
        check_habit_notifications()
        self.assertTrue(Notification.objects.filter(user=self.staff, meta_key__contains='habit').exists())

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_respects_in_app_off(self):
        NotificationPreferences.objects.create(user=self.staff, in_app=False)
        Habit.objects.create(user=self.staff, title='Leer', start_time=dt_time(10, 0), end_time=dt_time(11, 0))
        check_habit_notifications()
        self.assertFalse(Notification.objects.filter(user=self.staff).exists())

    @patch('apps.schedule.scheduler.timezone.now', _fake_now)
    def test_skips_zero_time(self):
        Habit.objects.create(user=self.staff, title='Sin horario', start_time=dt_time(0, 0), end_time=dt_time(0, 0))
        check_habit_notifications()
        self.assertFalse(Notification.objects.filter(user=self.staff).exists())
