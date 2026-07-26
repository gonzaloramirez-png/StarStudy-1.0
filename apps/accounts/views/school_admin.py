"""Vista del Dashboard de Administrador Escolar (SCHOOL_ADMIN).

Métricas globales del establecimiento, gestión de licencias, asignación de profesores.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.courses.models import Course, TeacherCourse, StudentCourse
from apps.accounts.decorators import role_required


@role_required('SCHOOL_ADMIN', 'ADMIN')
def school_dashboard(request):
    """Dashboard principal del administrador escolar."""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # === ESTADÍSTICAS GLOBALES ===
    total_users = User.objects.filter(is_active=True).count()
    total_teachers = User.objects.filter(role=User.Role.TEACHER, is_active=True).count()
    total_students = User.objects.filter(role=User.Role.STUDENT, is_active=True).count()
    total_courses = Course.objects.filter(status=Course.Status.ACTIVE).count()

    # Usuarios nuevos este mes
    new_users_month = User.objects.filter(
        date_joined__date__gte=thirty_days_ago,
    ).count()

    # Cursos activos
    active_courses = Course.objects.filter(status=Course.Status.ACTIVE)

    # Estudiantes por curso
    students_per_course = []
    for course in active_courses:
        count = StudentCourse.objects.filter(
            course=course,
            status=StudentCourse.Status.ACTIVE,
        ).count()
        students_per_course.append({
            'course': course,
            'student_count': count,
        })

    # === RENDIMIENTO GLOBAL ===
    from apps.tasks.models import Task
    from apps.gamification.models import QuizAttempt

    # Tasa de completación global
    total_tasks = Task.objects.filter(
        course__isnull=False,
        created_at__date__gte=thirty_days_ago,
    ).count()
    completed_tasks = Task.objects.filter(
        course__isnull=False,
        is_completed=True,
        completed_at__date__gte=thirty_days_ago,
    ).count()
    completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)

    # Promedio de notas global
    avg_score = Task.objects.filter(
        course__isnull=False,
        score__isnull=False,
        corrected_at__date__gte=thirty_days_ago,
    ).aggregate(avg=Avg('score'))['avg']
    avg_score = round(avg_score, 1) if avg_score else 0

    # === ACTIVIDAD RECIENTE ===
    recent_courses = Course.objects.filter(
        status=Course.Status.ACTIVE,
    ).order_by('-created_at')[:5]

    recent_teachers = User.objects.filter(
        role=User.Role.TEACHER,
        is_active=True,
    ).order_by('-date_joined')[:5]

    context = {
        'total_users': total_users,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'total_courses': total_courses,
        'new_users_month': new_users_month,
        'students_per_course': students_per_course,
        'completion_rate': completion_rate,
        'avg_score': avg_score,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'recent_courses': recent_courses,
        'recent_teachers': recent_teachers,
    }
    return render(request, 'accounts/school_dashboard.html', context)


@role_required('SCHOOL_ADMIN', 'ADMIN')
def manage_teachers(request):
    """Gestión de profesores: asignar a cursos/materias."""
    teachers = User.objects.filter(
        role__in=[User.Role.TEACHER, User.Role.STAFF],
        is_active=True,
    ).order_by('email')

    courses = Course.objects.filter(
        status=Course.Status.ACTIVE,
    ).order_by('name')

    # Asignaciones actuales
    assignments = TeacherCourse.objects.filter(
        course__status=Course.Status.ACTIVE,
    ).select_related('teacher', 'course').order_by('course__name', 'teacher__email')

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        course_id = request.POST.get('course_id')
        role = request.POST.get('role', TeacherCourse.Role.ASISTENTE)

        try:
            teacher = User.objects.get(pk=teacher_id)
            course = Course.objects.get(pk=course_id)
            assignment, created = TeacherCourse.objects.get_or_create(
                teacher=teacher,
                course=course,
                defaults={'role': role, 'assigned_by': request.user},
            )
            if created:
                messages.success(request, f'{teacher.email} asignado a {course.name}')
            else:
                messages.warning(request, f'{teacher.email} ya está asignado a {course.name}')
        except (User.DoesNotExist, Course.DoesNotExist):
            messages.error(request, 'Profesor o curso no válido')

        return redirect('manage_teachers')

    context = {
        'teachers': teachers,
        'courses': courses,
        'assignments': assignments,
        'role_choices': TeacherCourse.Role.choices,
    }
    return render(request, 'accounts/manage_teachers.html', context)
