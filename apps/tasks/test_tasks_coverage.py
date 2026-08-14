"""Tests de tareas: CRUD, asignación, completado y servicios."""
from datetime import timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from apps.accounts.tests import make_user
from apps.tasks.models import Task, Comment
from apps.tasks.services import create_task, complete_task, send_task_reminders


class TaskModelTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='profe@t.local', role='TEACHER')
        self.student = make_user(email='alumno@t.local', role='STUDENT')

    def test_task_str(self):
        task = Task.objects.create(title='Tarea', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        self.assertIn('Tarea', str(task))

    def test_task_orden_por_importancia(self):
        Task.objects.create(title='Low', importance='LOW', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        Task.objects.create(title='Critical', importance='CRITICAL', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        Task.objects.create(title='High', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        tasks = list(Task.objects.all().values_list('title', flat=True))
        self.assertEqual(tasks[0], 'Critical')
        self.assertEqual(tasks[1], 'High')
        self.assertEqual(tasks[2], 'Low')


class TaskServiceTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='profe2@t.local', role='TEACHER')
        self.student = make_user(email='alumno2@t.local', role='STUDENT')

    def test_create_task(self):
        from django.utils import timezone
        from apps.tasks.forms import TaskForm
        form_data = {
            'title': 'Nueva',
            'importance': 'MEDIUM',
            'deadline': (timezone.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'assigned_to': self.student.pk,
        }
        form = TaskForm(data=form_data, user=self.teacher)
        self.assertTrue(form.is_valid())
        task = create_task(form, self.teacher)
        self.assertIsNotNone(task.pk)
        self.assertFalse(task.is_completed)

    def test_complete_task(self):
        task = Task.objects.create(title='Completar', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        result = complete_task(task, self.student)
        self.assertIsNotNone(result)
        task.refresh_from_db()
        self.assertTrue(task.is_completed)
        self.assertIsNotNone(task.completed_at)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_task_reminders(self):
        Task.objects.create(title='Vence', importance='HIGH', deadline=timezone.now() + timedelta(hours=6), assigned_by=self.teacher, assigned_to=self.student)
        sent = send_task_reminders()
        self.assertEqual(sent, 1)


class TaskViewTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='views-profe@t.local', role='TEACHER')
        self.student = make_user(email='views-alumno@t.local', role='STUDENT')
        self.client.force_login(self.teacher)

    def test_task_list(self):
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

    def test_task_create_get(self):
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)

    def test_task_create_post(self):
        response = self.client.post(reverse('task_create'), {
            'title': 'Tarea desde test',
            'importance': 'HIGH',
            'deadline': (timezone.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'assigned_to': self.student.pk,
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Task.objects.filter(title='Tarea desde test').exists())

    def test_task_complete_view(self):
        task = Task.objects.create(title='Vista completar', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        response = self.client.post(reverse('task_complete', args=[task.pk]))
        self.assertIn(response.status_code, [200, 302])
        task.refresh_from_db()
        self.assertTrue(task.is_completed)


class CommentTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='com@t.local', role='TEACHER')
        self.student = make_user(email='com2@t.local', role='STUDENT')
        self.task = Task.objects.create(title='Con comentarios', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)

    def test_comment_str(self):
        comment = Comment.objects.create(task=self.task, user=self.student, text='Hola')
        self.assertIn('Hola', str(comment))


class CeleryTaskTests(TestCase):
    def test_send_task_deadline_reminders(self):
        from apps.tasks.tasks import send_task_deadline_reminders
        result = send_task_deadline_reminders()
        self.assertIsInstance(result, int)
