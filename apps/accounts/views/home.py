"""Vista home: dashboard principal del usuario con estadísticas y nivel.

Muestra tareas pendientes, vencidas, personales, y un sistema de nivel/xp
basado en tareas completadas (5 tareas = 1 nivel). Usa cache de 5 min.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.cache import get_home_stats, invalidate_home
from apps.tasks.models import Task
from apps.courses.models import Course, TeacherCourse, StudentCourse


@login_required
def home(request):
    user = request.user
    now = timezone.now()
    is_student = user.role == User.Role.STUDENT

    # Cursos del usuario para el selector en navbar
    if user.role in [User.Role.TEACHER, User.Role.STAFF, User.Role.PROGRAMMER, User.Role.ADMIN, User.Role.SCHOOL_ADMIN]:
        user_courses = Course.objects.filter(
            teacher_assignments__teacher=user,
            status=Course.Status.ACTIVE
        ).distinct().order_by('-created_at')
    elif is_student:
        user_courses = Course.objects.filter(
            student_enrollments__student=user,
            student_enrollments__status=StudentCourse.Status.ACTIVE
        ).distinct().order_by('-created_at')
    else:
        user_courses = Course.objects.none()

    # Curso seleccionado (desde query param o sesión)
    selected_course_pk = request.GET.get('course') or request.session.get('selected_course')
    selected_course = None
    if selected_course_pk:
        try:
            selected_course = user_courses.get(pk=selected_course_pk)
            request.session['selected_course'] = selected_course.pk
        except Course.DoesNotExist:
            pass

    def fetch_stats():
        HOME_FIELDS = ['id', 'title', 'importance', 'deadline', 'is_completed', 'is_personal', 'assigned_to_id', 'assigned_by_id']

        if is_student:
            all_tasks = Task.objects.select_related('assigned_to', 'assigned_by').only(*HOME_FIELDS).filter(assigned_to=user)
            base_tasks = all_tasks.filter(is_personal=False)
        else:
            all_tasks = Task.objects.select_related('assigned_to', 'assigned_by').only(*HOME_FIELDS).filter(assigned_by=user)
            base_tasks = all_tasks.filter(is_personal=False)

        # Si hay curso seleccionado, filtrar tareas de ese curso
        if selected_course:
            base_tasks = base_tasks.filter(course=selected_course)

        counts = base_tasks.aggregate(
            pending=Count('id', filter=Q(is_completed=False)),
            overdue=Count('id', filter=Q(is_completed=False, deadline__lt=now)),
            completed=Count('id', filter=Q(is_completed=True)),
        )

        personal_count = all_tasks.filter(is_personal=True, is_completed=False).count()

        recent = list(base_tasks.filter(is_completed=False).order_by('deadline')[:5])
        recent_pending = recent[:3]

        counts['personal'] = personal_count
        counts['recent'] = recent
        counts['recent_pending'] = recent_pending
        return counts

    stats = get_home_stats(user.pk, fetch_stats)

    completed_count = stats['completed']
    level = completed_count // 5 + 1
    xp = completed_count % 5

    context = {
        'recent': stats['recent'],
        'pending': stats['pending'],
        'overdue': stats['overdue'],
        'recent_pending': stats['recent_pending'],
        'level': level,
        'xp': xp,
        'xp_percent': xp * 20,
        'next_level_xp': 5,
        'completed_count': completed_count,
        'personal_count': stats['personal'],
        'user_courses': user_courses,
        'selected_course': selected_course,
    }

    return render(request, 'home.html', context)