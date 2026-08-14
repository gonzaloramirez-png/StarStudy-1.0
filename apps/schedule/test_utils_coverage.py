"""Tests de schedule utils."""
from datetime import time
from django.test import TestCase
from apps.schedule.utils import build_schedule_table


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
