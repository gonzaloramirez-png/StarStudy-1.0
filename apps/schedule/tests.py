"""Tests de schedule: validación del formulario y permisos."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.schedule.models import ScheduleEntry
from apps.schedule.forms import ScheduleEntryForm

User = get_user_model()


def make_user(email, role):
    return User.objects.create_user(
        username=email.split('@')[0] + '_' + role.lower(),
        email=email,
        password='claveSegura123',
        role=role,
    )


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
