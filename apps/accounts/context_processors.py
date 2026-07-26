"""Context processors para StarStudy.

Provee variables globales a todas las plantillas:
- user_courses: cursos del usuario actual
- selected_course: curso seleccionado en sesión
"""
from django.conf import settings
from django.db.models import Count, Q
from apps.courses.models import Course, StudentCourse


def user_courses(request):
    """Retorna cursos del usuario y curso seleccionado actual.

    Funciona para usuarios autenticados con rol TEACHER, STAFF, PROGRAMMER, STUDENT.
    """
    if not request.user.is_authenticated:
        return {'user_courses': [], 'selected_course': None}

    user = request.user
    selected_course_pk = request.GET.get('course') or request.session.get('selected_course')

    # Obtener cursos según rol
    if user.role in [user.Role.TEACHER, user.Role.STAFF, user.Role.PROGRAMMER]:
        user_courses = Course.objects.filter(
            teacher_assignments__teacher=user,
            status=Course.Status.ACTIVE
        ).annotate(
            student_count=Count('student_enrollments', filter=Q(student_enrollments__status=StudentCourse.Status.ACTIVE))
        ).distinct().order_by('-created_at')
    elif user.role == user.Role.STUDENT:
        user_courses = Course.objects.filter(
            student_enrollments__student=user,
            student_enrollments__status=StudentCourse.Status.ACTIVE
        ).annotate(
            student_count=Count('student_enrollments', filter=Q(student_enrollments__status=StudentCourse.Status.ACTIVE))
        ).distinct().order_by('-created_at')
    else:
        user_courses = Course.objects.none()

    # Resolver curso seleccionado
    selected_course = None
    if selected_course_pk:
        try:
            selected_course = user_courses.get(pk=selected_course_pk)
            request.session['selected_course'] = selected_course.pk
        except Course.DoesNotExist:
            # Limpiar sesión si el curso ya no existe o no pertenece al usuario
            request.session.pop('selected_course', None)

    return {
        'user_courses': user_courses,
        'selected_course': selected_course,
    }


def site_settings(request):
    """Configuraciones globales del sitio."""
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'StarStudy'),
        'site_version': getattr(settings, 'SITE_VERSION', '1.0.0'),
    }