"""Vista de tabla de notas inline (estilo Excel) para corregir tareas rápido.

- grade_table: vista principal con tabla editable de todas las tareas de un curso
- grade_update: endpoint HTMX para actualizar nota/status/XP inline
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, F
from django.utils import timezone
import json

from apps.tasks.models import Task, CommentSnippet
from apps.courses.models import Course, TeacherCourse, StudentCourse
from apps.accounts.models import User
from apps.accounts.decorators import role_required
from apps.tasks.services import add_comment


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def grade_table(request, course_pk):
    """Tabla de notas estilo Excel para un curso.

    Muestra todas las tareas del curso con columnas editables:
    - Estudiante
    - Tarea
    - Estado (select)
    - Nota 0-100 (input number)
    - XP (calculado)
    - Deadline
    """
    course = get_object_or_404(Course, pk=course_pk)

    # Verificar acceso
    is_teacher = TeacherCourse.objects.filter(
        course=course, teacher=request.user,
        role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).exists()
    if not is_teacher and request.user.role != User.Role.PROGRAMMER:
        return render(request, '403.html', status=403)

    # Filtros
    task_filter = request.GET.get('task')
    status_filter = request.GET.get('status')
    student_filter = request.GET.get('student')
    show_only = request.GET.get('show', 'all')  # all, pending, corrected, ungraded

    # Tareas del curso
    tasks = Task.objects.filter(
        course=course,
        is_personal=False,
    ).select_related('assigned_to', 'assigned_by').order_by('-deadline')

    if task_filter:
        tasks = tasks.filter(pk=task_filter)
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if student_filter:
        tasks = tasks.filter(assigned_to_id=student_filter)

    # Filtrar por estado de calificación
    if show_only == 'pending':
        tasks = tasks.filter(is_completed=True, status__in=[Task.Status.PENDING, Task.Status.IN_REVIEW])
    elif show_only == 'ungraded':
        tasks = tasks.filter(score__isnull=True)
    elif show_only == 'corrected':
        tasks = tasks.filter(status=Task.Status.CORRECTED)

    # Estudiantes del curso
    students = User.objects.filter(
        student_courses__course=course,
        student_courses__status=StudentCourse.Status.ACTIVE
    ).order_by('email')

    # Snippets del profesor
    snippets = CommentSnippet.objects.filter(teacher=request.user).order_by('category', 'title')

    # Stats rápidas
    from django.db.models import Count, Avg
    stats = tasks.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status__in=[Task.Status.PENDING, Task.Status.IN_REVIEW], is_completed=True)),
        corrected=Count('id', filter=Q(status=Task.Status.CORRECTED)),
        ungraded=Count('id', filter=Q(score__isnull=True)),
        avg_score=Avg('score'),
    )

    from django.utils import timezone
    now = timezone.now()
    urgent_date = now + timezone.timedelta(days=3)

    context = {
        'course': course,
        'tasks': tasks,
        'students': students,
        'snippets': snippets,
        'stats': stats,
        'show_only': show_only,
        'status_choices': Task.Status.choices,
        'student_filter': student_filter,
        'task_filter': task_filter,
        'now': now,
        'urgent_date': urgent_date,
    }
    return render(request, 'tasks/grade_table.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def grade_update(request, task_pk):
    """Endpoint HTMX para actualizar calificación de una tarea inline.

    Acepta: score (0-100), status, comment
    Retorna: JSON con resultado
    """
    task = get_object_or_404(Task, pk=task_pk)

    # Verificar que es profesor del curso
    is_teacher = TeacherCourse.objects.filter(
        course=task.course, teacher=request.user,
        role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).exists()
    if not is_teacher and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    score = request.POST.get('score')
    status = request.POST.get('status')
    comment = request.POST.get('comment', '').strip()

    # Actualizar nota
    if score is not None and score != '':
        try:
            score_val = int(score)
            if score_val < 0 or score_val > 100:
                return JsonResponse({'success': False, 'error': 'Nota debe ser 0-100'}, status=400)
            task.score = score_val
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Nota inválida'}, status=400)

    # Actualizar estado
    if status and status in Task.Status.values:
        task.status = status
        if status == Task.Status.CORRECTED:
            task.corrected_at = timezone.now()
            task.corrected_by = request.user

    task.save(update_fields=['score', 'status', 'corrected_at', 'corrected_by', 'updated_at'])

    # Agregar comentario si existe
    if comment:
        add_comment(task, request.user, comment)

    # Calcular XP basado en nota (0-100 → 0-25 XP)
    xp = 0
    if task.score is not None:
        xp = round(task.score * 0.25)

    return JsonResponse({
        'success': True,
        'task_id': task.pk,
        'score': task.score,
        'status': task.get_status_display(),
        'status_value': task.status,
        'xp': xp,
        'corrected_at': task.corrected_at.strftime('%d/%m %H:%M') if task.corrected_at else None,
    })


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def grade_bulk_update(request, course_pk):
    """Actualizar múltiples tareas a la vez (batch save)."""
    course = get_object_or_404(Course, pk=course_pk)

    is_teacher = TeacherCourse.objects.filter(
        course=course, teacher=request.user,
        role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).exists()
    if not is_teacher and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    updates = request.POST.get('updates')
    if not updates:
        return JsonResponse({'success': False, 'error': 'No hay datos'}, status=400)

    try:
        updates_list = json.loads(updates)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    updated_count = 0
    for item in updates_list:
        task_id = item.get('task_id')
        score = item.get('score')
        status = item.get('status')

        try:
            task = Task.objects.get(pk=task_id, course=course)
        except Task.DoesNotExist:
            continue

        if score is not None and score != '':
            try:
                task.score = int(score)
            except (ValueError, TypeError):
                pass

        if status and status in Task.Status.values:
            task.status = status
            if status == Task.Status.CORRECTED:
                task.corrected_at = timezone.now()
                task.corrected_by = request.user

        task.save(update_fields=['score', 'status', 'corrected_at', 'corrected_by', 'updated_at'])
        updated_count += 1

    return JsonResponse({
        'success': True,
        'updated': updated_count,
        'message': f'{updated_count} tareas actualizadas',
    })
