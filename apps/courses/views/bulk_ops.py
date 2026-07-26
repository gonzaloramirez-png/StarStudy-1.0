"""Vistas de clonación de cursos y asignación masiva de tareas."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.accounts.models import User
from apps.courses.models import Course, CourseCode, TeacherCourse, StudentCourse
from apps.tasks.models import Task


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def course_clone(request, pk):
    """Clonar curso existente como plantilla para nueva sección."""
    original = get_object_or_404(Course, pk=pk)

    # Verificar acceso
    if request.user.role in (User.Role.TEACHER, User.Role.STAFF):
        if not original.teacher_assignments.filter(teacher=request.user).exists():
            messages.error(request, 'No tienes acceso a este curso')
            return redirect('course_list')

    if request.method == 'POST':
        new_name = request.POST.get('name', f'{original.name} (Copia)')
        academic_year = request.POST.get('academic_year', original.academic_year)
        clone_tasks = request.POST.get('clone_tasks') == 'on'

        new_course = original.clone(
            new_name=new_name,
            academic_year=academic_year,
            created_by=request.user,
        )

        if not clone_tasks:
            from apps.tasks.models import Task
            Task.objects.filter(course=new_course).delete()

        # Asignar al creador como titular
        TeacherCourse.objects.get_or_create(
            teacher=request.user,
            course=new_course,
            defaults={'role': TeacherCourse.Role.TITULAR, 'assigned_by': request.user},
        )

        messages.success(request, f'Curso "{new_course.name}" creado como copia de "{original.name}"')
        return redirect('course_detail', pk=new_course.pk)

    context = {
        'original': original,
        'task_count': original.tasks.count(),
    }
    return render(request, 'courses/course_clone.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def bulk_task_assign(request, pk):
    """Asignar una tarea a múltiples estudiantes de un curso."""
    course = get_object_or_404(Course, pk=pk)

    # Verificar acceso del profesor
    if request.user.role in (User.Role.TEACHER, User.Role.STAFF):
        if not course.teacher_assignments.filter(teacher=request.user).exists():
            return JsonResponse({'success': False, 'error': 'Sin acceso'}, status=403)

    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '')
    importance = request.POST.get('importance', Task.Importance.MEDIUM)
    deadline = request.POST.get('deadline')
    student_ids = request.POST.getlist('student_ids')

    if not title or not deadline:
        messages.error(request, 'Título y fecha límite son obligatorios')
        return redirect('course_detail', pk=pk)

    if not student_ids:
        messages.warning(request, 'Selecciona al menos un estudiante')
        return redirect('course_detail', pk=pk)

    enrolled_students = StudentCourse.objects.filter(
        course=course,
        status=StudentCourse.Status.ACTIVE,
        student_id__in=student_ids,
    ).select_related('student')

    created_count = 0
    for enrollment in enrolled_students:
        Task.objects.create(
            title=title,
            description=description,
            importance=importance,
            deadline=deadline,
            assigned_by=request.user,
            assigned_to=enrollment.student,
            course=course,
        )
        created_count += 1

    messages.success(request, f'Tarea "{title}" asignada a {created_count} estudiantes')
    return redirect('course_detail', pk=pk)
