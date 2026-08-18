"""Tests de tasks: asignación, completado, XP, notificaciones y recordatorios."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Notification
from apps.tasks.forms import TaskForm
from apps.tasks.models import Task, Comment
from apps.tasks.services import (
    add_comment,
    apply_filters,
    complete_task,
    create_task,
    get_task_queryset,
    send_task_reminders,
)
from apps.tasks.tasks import send_task_deadline_reminders

User = get_user_model()


def make_user(email, role, **kwargs):
    return User.objects.create_user(
        username=email.split('@')[0] + '_' + role.lower(),
        email=email,
        password='claveSegura123',
        role=role,
        **kwargs,
    )


def make_task(assigned_by, assigned_to, **kwargs):
    defaults = {
        'title': 'Tarea de prueba',
        'importance': Task.Importance.MEDIUM,
        'deadline': timezone.now() + timedelta(days=1),
    }
    defaults.update(kwargs)
    return Task.objects.create(assigned_by=assigned_by, assigned_to=assigned_to, **defaults)


class TaskAssignmentTests(TestCase):
    def setUp(self):
        self.teacher = make_user('prof@starstudy.local', 'TEACHER')
        self.student = make_user('alumno@starstudy.local', 'STUDENT')
        # Limpiamos la notificación de bienvenida que crea la señal post_save
        Notification.objects.all().delete()

    def test_asignar_tarea_notifica_al_estudiante(self):
        task = make_task(self.teacher, self.student)
        notif = Notification.objects.filter(user=self.student).first()
        self.assertIsNotNone(notif)
        self.assertIn(task.title, notif.message)
        self.assertIn('te asignó', notif.message)

    def test_tarea_personal_no_notifica(self):
        make_task(self.teacher, self.teacher, is_personal=True)
        self.assertEqual(Notification.objects.filter(user=self.teacher).count(), 0)

    def test_completar_tarea_marca_fecha_y_notifica_al_creador(self):
        task = make_task(self.teacher, self.student)
        self.client.force_login(self.student)
        self.client.post(reverse('task_complete', args=[task.pk]))
        task.refresh_from_db()
        self.assertTrue(task.is_completed)
        self.assertIsNotNone(task.completed_at)
        notif = Notification.objects.filter(user=self.teacher).order_by('-created_at').first()
        self.assertIsNotNone(notif)
        self.assertIn('completó', notif.message)


class TaskListViewTests(TestCase):
    def setUp(self):
        self.teacher = make_user('prof2@starstudy.local', 'TEACHER')
        self.student = make_user('alumno2@starstudy.local', 'STUDENT')

    def test_estudiante_solo_ve_sus_tareas(self):
        otro = make_user('otro@starstudy.local', 'STUDENT')
        make_task(self.teacher, self.student)
        make_task(self.teacher, otro)
        self.client.force_login(self.student)
        response = self.client.get(reverse('task_list'))
        self.assertEqual(len(response.context['tasks'].object_list), 1)

    def test_profesor_solo_ve_tareas_que_asigno(self):
        otro_prof = make_user('prof3@starstudy.local', 'TEACHER')
        make_task(self.teacher, self.student)
        make_task(otro_prof, self.student)
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('task_list'))
        self.assertEqual(len(response.context['tasks'].object_list), 1)


class TaskHtmxTests(TestCase):
    def setUp(self):
        self.teacher = make_user('prof-hx@starstudy.local', 'TEACHER')
        self.student = make_user('alumno-hx@starstudy.local', 'STUDENT')
        # Limpiamos la notificación de bienvenida que crea la señal post_save
        Notification.objects.all().delete()

    def test_lista_htmx_devuelve_parcial(self):
        make_task(self.teacher, self.student)
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('task_list'), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="task-list-container"')
        self.assertContains(response, 'id="task-list-indicator"')
        self.assertContains(response, 'Tarea de prueba')

    def test_filtro_htmx_por_importancia(self):
        make_task(self.teacher, self.student, title='Alta', importance=Task.Importance.HIGH)
        make_task(self.teacher, self.student, title='Media', importance=Task.Importance.MEDIUM)
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse('task_list'), {'importance': 'HIGH'}, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Alta')
        self.assertNotContains(response, 'Media')

    def test_create_htmx_get_devuelve_modal(self):
        self.client.force_login(self.teacher)
        response = self.client.get(
            reverse('task_create') + '?personal=1', HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'task-modal')

    def test_create_htmx_post_valido_responde_204(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('task_create') + '?personal=1',
            {'title': 'Tarea HTMX', 'importance': 'MEDIUM', 'deadline': '2026-12-31T23:59'},
            HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['HX-Redirect'], reverse('task_personal'))
        self.assertIn('toast:', response['HX-Trigger'])

    def test_create_htmx_post_invalido_devuelve_422(self):
        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse('task_create') + '?personal=1',
            {'title': '', 'importance': 'MEDIUM'},
            HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 422)
        self.assertIn(b'task-modal', response.content)

    def test_detalle_htmx_devuelve_parcial_de_comentarios(self):
        task = make_task(self.teacher, self.student)
        Comment.objects.create(task=task, user=self.student, text='Hola profe')
        self.client.force_login(self.student)
        response = self.client.get(reverse('task_detail', args=[task.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Detalle de tarea')
        self.assertContains(response, 'Hola profe')

    def test_comment_create_htmx_muestra_comentario(self):
        task = make_task(self.teacher, self.student)
        self.client.force_login(self.student)
        response = self.client.post(
            reverse('comment_create', args=[task.pk]),
            {'text': 'Comentario nuevo'},
            HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comentario nuevo')
        self.assertIn('toast:', response['HX-Trigger'])

    def test_comment_create_htmx_vacio_devuelve_422(self):
        task = make_task(self.teacher, self.student)
        self.client.force_login(self.student)
        response = self.client.post(
            reverse('comment_create', args=[task.pk]),
            {'text': ''},
            HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 422)


class TaskReminderTests(TestCase):
    def setUp(self):
        self.teacher = make_user('prof-rec@starstudy.local', 'TEACHER')
        self.student = make_user('alumno-rec@starstudy.local', 'STUDENT')
        Notification.objects.all().delete()

    def make_task_reminder(self, **kwargs):
        defaults = {'deadline': timezone.now() + timedelta(hours=6)}
        defaults.update(kwargs)
        return make_task(self.teacher, self.student, **defaults)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_envia_recordatorio_al_estudiante(self):
        task = self.make_task_reminder()
        sent = send_task_reminders()
        self.assertEqual(sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.student.email])
        self.assertIn(task.title, mail.outbox[0].subject)
        task.refresh_from_db()
        self.assertTrue(task.reminder_sent)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_tarea_personal_recorda_al_creador(self):
        make_task(
            self.teacher, self.teacher,
            is_personal=True,
            deadline=timezone.now() + timedelta(hours=6))
        sent = send_task_reminders()
        self.assertEqual(sent, 1)
        self.assertEqual(mail.outbox[0].to, [self.teacher.email])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_no_reenvia_si_ya_se_aviso(self):
        task = self.make_task_reminder(reminder_sent=True)
        sent = send_task_reminders()
        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)
        task.refresh_from_db()
        self.assertTrue(task.reminder_sent)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_ignora_fuera_de_la_ventana(self):
        self.make_task_reminder(deadline=timezone.now() + timedelta(hours=48))
        self.make_task_reminder(deadline=timezone.now() - timedelta(hours=1))
        sent = send_task_reminders()
        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_ignora_tarea_completada(self):
        self.make_task_reminder(is_completed=True)
        sent = send_task_reminders()
        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_ventana_configurable(self):
        self.make_task_reminder(deadline=timezone.now() + timedelta(hours=6))
        sent = send_task_reminders(window_hours=2)
        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
    )
    def test_tarea_celery_envia_via_eager(self):
        self.make_task_reminder()
        result = send_task_deadline_reminders.delay()
        self.assertEqual(result.get(), 1)
        self.assertEqual(len(mail.outbox), 1)


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

    def test_create_task(self):
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
        response = self.client.post(reverse('task_create'), {
            'title': 'Tarea desde test',
            'importance': 'HIGH',
            'deadline': (timezone.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'assigned_to': self.student.pk,
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Task.objects.filter(title='Tarea desde test').exists())

    def test_task_complete(self):
        self.client.force_login(self.student)
        task = Task.objects.create(title='Completar', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
        response = self.client.post(reverse('task_complete', args=[task.pk]))
        self.assertIn(response.status_code, [200, 302])
        task.refresh_from_db()
        self.assertTrue(task.is_completed)

    def test_task_complete_view(self):
        task = Task.objects.create(title='Vista completar', importance='HIGH', deadline=timezone.now(), assigned_by=self.teacher, assigned_to=self.student)
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
        result = send_task_deadline_reminders()
        self.assertIsInstance(result, int)