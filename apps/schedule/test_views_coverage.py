"""Tests de schedule views."""
from django.test import TestCase
from django.urls import reverse
from apps.accounts.tests import make_user
from apps.schedule.models import ScheduleEntry


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
