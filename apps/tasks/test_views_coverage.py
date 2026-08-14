"""Tests de task views: CRUD, filtros, comentarios."""
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.accounts.tests import make_user
from apps.tasks.models import Task, Comment
from apps.tasks.services import get_task_queryset, apply_filters, create_task, complete_task, delete_task, add_comment


class TaskServiceTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='ts-svc@t.local', role='TEACHER')
        self.student = make_user(email='ts-svc2@t.local', role='STUDENT')

    def test_get_task_queryset_teacher(self):
        Task.objects.create(title='T1', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        qs = get_task_queryset(self.teacher, is_personal=False)
        self.assertEqual(qs.count(), 1)

    def test_get_task_queryset_student(self):
        Task.objects.create(title='T2', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        qs = get_task_queryset(self.student, is_personal=False)
        self.assertEqual(qs.count(), 1)

    def test_apply_filters_importance(self):
        qs = Task.objects.filter(assigned_to=self.student)
        Task.objects.create(title='Low', importance='LOW', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        Task.objects.create(title='High', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        filtered = apply_filters(qs, importance='HIGH')
        self.assertEqual(filtered.count(), 1)

    def test_apply_filters_status_pending(self):
        Task.objects.create(title='Done', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student, is_completed=True)
        Task.objects.create(title='Pending', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        qs = Task.objects.filter(assigned_to=self.student)
        filtered = apply_filters(qs, status='pending')
        self.assertEqual(filtered.count(), 1)

    def test_apply_filters_status_completed(self):
        Task.objects.create(title='Done', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student, is_completed=True)
        qs = Task.objects.filter(assigned_to=self.student)
        filtered = apply_filters(qs, status='completed')
        self.assertEqual(filtered.count(), 1)

    def test_apply_filters_status_overdue(self):
        Task.objects.create(title='Overdue', importance='HIGH', deadline=timezone.now() - timedelta(hours=1), assigned_by=self.teacher, assigned_to=self.student)
        qs = Task.objects.filter(assigned_to=self.student)
        filtered = apply_filters(qs, status='overdue', now=timezone.now())
        self.assertEqual(filtered.count(), 1)

    def test_add_comment(self):
        task = Task.objects.create(title='Con comment', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        comment = add_comment(task, self.student, 'Hola')
        self.assertIsNotNone(comment.pk)


class TaskViewTests(TestCase):
    def setUp(self):
        self.teacher = make_user(email='ts-view@t.local', role='TEACHER')
        self.student = make_user(email='ts-view-s@t.local', role='STUDENT')

    def test_task_list(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

    def test_task_personal(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('task_personal'))
        self.assertEqual(response.status_code, 200)

    def test_task_detail(self):
        self.client.force_login(self.teacher)
        task = Task.objects.create(title='Detalle', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        response = self.client.get(reverse('task_detail', args=[task.pk]))
        self.assertEqual(response.status_code, 200)

    def test_task_create_get(self):
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)

    def test_task_create_post(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('task_create'), {
            'title': 'Nueva tarea',
            'importance': 'HIGH',
            'deadline': (timezone.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'assigned_to': self.student.pk,
        })
        self.assertIn(response.status_code, [200, 302])

    def test_task_complete(self):
        self.client.force_login(self.student)
        task = Task.objects.create(title='Completar', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        response = self.client.post(reverse('task_complete', args=[task.pk]))
        self.assertIn(response.status_code, [200, 302])
        task.refresh_from_db()
        self.assertTrue(task.is_completed)

    def test_task_delete(self):
        self.client.force_login(self.teacher)
        task = Task.objects.create(title='Eliminar', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        response = self.client.post(reverse('task_delete', args=[task.pk]))
        self.assertIn(response.status_code, [200, 302])
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_comment_create(self):
        self.client.force_login(self.student)
        task = Task.objects.create(title='Comentar', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        response = self.client.post(reverse('comment_create', args=[task.pk]), {'text': 'Comentario'})
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Comment.objects.filter(task=task).exists())
