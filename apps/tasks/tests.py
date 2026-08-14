"""Tests de tasks: asignación, completado, XP, notificaciones y recordatorios."""
from django.test import TestCase
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.tasks.models import Task, Comment
from apps.accounts.models import Notification
from apps.tasks.services import send_task_reminders
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
