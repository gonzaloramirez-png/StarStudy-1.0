"""Tests de schedule: servicios, utils y modelos."""
from datetime import time
from django.test import TestCase
from django.urls import reverse
from apps.accounts.tests import make_user
from apps.schedule.models import ScheduleEntry
from apps.schedule.services import (
    get_schedule_context, add_schedule_entry, delete_schedule_entry,
    _group_entries_by_day, _base_context, _fetch_schedule,
)
from apps.schedule.utils import build_schedule_table


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
        from apps.schedule.forms import ScheduleEntryForm
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
