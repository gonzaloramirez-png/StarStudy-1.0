"""Vistas de courses: CRUD de cursos, códigos de invitación y gestión de asignaciones."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.urls import reverse

login_require = login_required

from apps.accounts.models import User
from apps.courses.models import Course, CourseCode, TeacherCourse, StudentCourse


def _require_teacher(user):
    """Verifica que el usuario sea profesor o personal."""
    return user.role in [User.Role.TEACHER, User.Role.STAFF, User.Role.PROGRAMMER]


def _get_teacher_courses(user):
    """Retorna cursos donde el usuario es profesor titular o asistente."""
    return Course.objects.filter(
        teacher_assignments__teacher=user,
        teacher_assignments__role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).distinct()


@login_required
def course_list(request):
    """Lista de cursos del profesor con filtros y paginación."""
    if not _require_teacher(request.user):
        messages.error(request, 'Acceso denegado. Solo profesores.')
        return redirect('home')

    courses = _get_teacher_courses(request.user).annotate(
        student_count=Count('student_enrollments', filter=Q(student_enrollments__status=StudentCourse.Status.ACTIVE)),
        teacher_count=Count('teacher_assignments')
    )

    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        courses = courses.filter(status=status_filter)

    search = request.GET.get('q')
    if search:
        courses = courses.filter(Q(name__icontains=search) | Q(description__icontains=search))

    # Paginación
    paginator = Paginator(courses, 10)
    page = request.GET.get('page')
    courses_page = paginator.get_page(page)

    context = {
        'courses': courses_page,
        'status_choices': Course.Status.choices,
        'current_status': status_filter,
        'search_query': search,
    }
    return render(request, 'courses/course_list.html', context)


@login_required
def course_create(request):
    """Crear nuevo curso (solo profesores)."""
    if not _require_teacher(request.user):
        messages.error(request, 'Acceso denegado.')
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        academic_year = request.POST.get('academic_year', '').strip() or str(timezone.now().year)

        if not name:
            messages.error(request, 'El nombre del curso es obligatorio.')
        else:
            course = Course.objects.create(
                name=name,
                description=description,
                academic_year=academic_year,
                created_by=request.user,
            )
            # Asignar al creador como titular
            TeacherCourse.objects.create(
                teacher=request.user,
                course=course,
                role=TeacherCourse.Role.TITULAR,
                assigned_by=request.user
            )
            # Generar código de invitación
            CourseCode.objects.create(course=course)
            messages.success(request, f'Curso "{course.name}" creado con código de invitación.')
            return redirect('courses:course_detail', pk=course.pk)

    context = {'academic_year': str(timezone.now().year)}
    return render(request, 'courses/course_form.html', context)


@login_required
def course_detail(request, pk):
    """Detalle del curso con pestañas: info, estudiantes, profesores, código."""
    course = get_object_or_404(Course, pk=pk)

    # Verificar acceso
    is_teacher = _get_teacher_courses(request.user).filter(pk=pk).exists()
    is_student = StudentCourse.objects.filter(student=request.user, course=course, status=StudentCourse.Status.ACTIVE).exists()

    if not (is_teacher or is_student or request.user.role == User.Role.PROGRAMMER):
        messages.error(request, 'No tienes acceso a este curso.')
        return redirect('courses:course_list')

    # Obtener código de invitación
    invite_code = None
    if hasattr(course, 'invite_code'):
        invite_code = course.invite_code

    # Estudiantes
    students = StudentCourse.objects.filter(course=course).select_related('student', 'enrolled_via_code')

    # Profesores
    teachers = TeacherCourse.objects.filter(course=course).select_related('teacher', 'assigned_by')

    # Estadísticas de productividad del curso
    from apps.gamification.models import Ranking
    course_stats = Ranking.get_course_stats(course)

    context = {
        'course': course,
        'invite_code': invite_code,
        'students': students,
        'teachers': teachers,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'teacher_role_choices': TeacherCourse.Role.choices,
        'student_status_choices': StudentCourse.Status.choices,
        'course_stats': course_stats,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def course_edit(request, pk):
    """Editar curso (solo titular)."""
    course = get_object_or_404(Course, pk=pk)

    # Verificar que es titular
    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        messages.error(request, 'Solo el profesor titular puede editar el curso.')
        return redirect('courses:course_detail', pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        academic_year = request.POST.get('academic_year', '').strip()

        if not name:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            course.name = name
            course.description = description
            course.academic_year = academic_year
            course.save(update_fields=['name', 'description', 'academic_year', 'updated_at'])
            messages.success(request, 'Curso actualizado.')
            return redirect('courses:course_detail', pk=pk)

    context = {'course': course}
    return render(request, 'courses/course_form.html', context)


@login_require
@require_POST
def course_archive(request, pk):
    """Archivar/desarchivar curso."""
    course = get_object_or_404(Course, pk=pk)

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    if course.status == Course.Status.ACTIVE:
        course.archive()
        return JsonResponse({'success': True, 'status': 'archived', 'message': 'Curso archivado'})
    else:
        course.restore()
        return JsonResponse({'success': True, 'status': 'active', 'message': 'Curso restaurado'})


@login_required
def course_delete(request, pk):
    """Eliminar curso (solo titular, POST)."""
    course = get_object_or_404(Course, pk=pk)

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        messages.error(request, 'Sin permisos.')
        return redirect('courses:course_list')

    if request.method == 'POST':
        name = course.name
        course.delete()
        messages.success(request, f'Curso "{name}" eliminado.')
        return redirect('courses:course_list')

    return render(request, 'courses/course_confirm_delete.html', {'course': course})


# === CÓDIGOS DE INVITACIÓN ===

@login_required
@require_POST
def invite_code_regenerate(request, pk):
    """Regenerar código de invitación del curso."""
    course = get_object_or_404(Course, pk=pk)

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    if not hasattr(course, 'invite_code'):
        CourseCode.objects.create(course=course)
        invite_code = course.invite_code
        old_code = None
    else:
        invite_code = course.invite_code
        old_code = invite_code.code
        invite_code.regenerate()

    return JsonResponse({
        'success': True,
        'code': invite_code.code,
        'old_code': old_code,
        'status': invite_code.get_status_display(),
    })


@login_required
@require_POST
def invite_code_toggle(request, pk):
    """Abrir/cerrar código de invitación."""
    course = get_object_or_404(Course, pk=pk)

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    if not hasattr(course, 'invite_code'):
        return JsonResponse({'success': False, 'error': 'Código no existe'}, status=404)

    invite_code = course.invite_code
    action = request.POST.get('action', 'toggle')

    if action == 'close' or (action == 'toggle' and invite_code.status == CourseCode.Status.OPEN):
        invite_code.close()
        new_status = 'closed'
    elif action == 'open' or (action == 'toggle' and invite_code.status == CourseCode.Status.CLOSED):
        invite_code.open()
        new_status = 'open'
    else:
        new_status = invite_code.status

    return JsonResponse({
        'success': True,
        'status': new_status,
        'status_display': invite_code.get_status_display(),
    })


# === GESTIÓN DE ESTUDIANTES ===

@login_required
@require_POST
def student_enroll_code(request):
    """Inscribir estudiante usando código de invitación."""
    if request.user.role != User.Role.STUDENT:
        return JsonResponse({'success': False, 'error': 'Solo estudiantes'}, status=403)

    code = request.POST.get('code', '').strip().upper()
    if not code:
        return JsonResponse({'success': False, 'error': 'Código requerido'}, status=400)

    invite_code = CourseCode.objects.filter(code=code).select_related('course').first()
    if not invite_code:
        return JsonResponse({'success': False, 'error': 'Código inválido'}, status=404)

    if not invite_code.is_valid():
        return JsonResponse({'success': False, 'error': 'Código expirado o cerrado'}, status=400)

    course = invite_code.course

    # Verificar si ya está inscrito
    enrollment, created = StudentCourse.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={
            'status': StudentCourse.Status.ACTIVE,
            'enrolled_via_code': invite_code,
        }
    )

    if not created:
        if enrollment.status == StudentCourse.Status.ACTIVE:
            return JsonResponse({'success': False, 'error': 'Ya estás inscrito en este curso'}, status=400)
        elif enrollment.status == StudentCourse.Status.WITHDRAWN:
            enrollment.activate()
            enrollment.enrolled_via_code = invite_code
            enrollment.save(update_fields=['status', 'withdrawn_at', 'enrolled_via_code'])
        elif enrollment.status == StudentCourse.Status.BLOCKED:
            return JsonResponse({'success': False, 'error': 'Tu inscripción está bloqueada. Contacta al profesor.'}, status=403)

    invite_code.use_code()
    return JsonResponse({
        'success': True,
        'course': course.name,
        'message': f'Inscrito en "{course.name}" correctamente'
    })


@login_required
@require_POST
def student_status_update(request, pk):
    """Actualizar estado de estudiante en curso (bloquear/activar/retirar)."""
    enrollment = get_object_or_404(StudentCourse, pk=pk)
    course = enrollment.course

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    action = request.POST.get('action')
    if action == 'block':
        enrollment.block()
        status = 'blocked'
    elif action == 'activate':
        enrollment.activate()
        status = 'active'
    elif action == 'withdraw':
        enrollment.withdraw()
        status = 'withdrawn'
    else:
        return JsonResponse({'success': False, 'error': 'Acción inválida'}, status=400)

    return JsonResponse({
        'success': True,
        'status': status,
        'status_display': enrollment.get_status_display(),
    })


@login_required
@require_POST
def student_remove(request, pk):
    """Eliminar inscripción de estudiante (solo titular)."""
    enrollment = get_object_or_404(StudentCourse, pk=pk)
    course = enrollment.course

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    student_name = enrollment.student.get_full_name() or enrollment.student.email
    enrollment.delete()

    return JsonResponse({
        'success': True,
        'message': f'{student_name} retirado del curso'
    })


# === GESTIÓN DE PROFESORES ===

@login_required
@require_POST
def teacher_assign(request, pk):
    """Asignar profesor asistente a curso."""
    course = get_object_or_404(Course, pk=pk)

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    teacher_email = request.POST.get('teacher_email', '').strip().lower()
    role = request.POST.get('role', TeacherCourse.Role.ASISTENTE)

    if not teacher_email:
        return JsonResponse({'success': False, 'error': 'Email requerido'}, status=400)

    teacher = User.objects.filter(email=teacher_email, role__in=[User.Role.TEACHER, User.Role.STAFF]).first()
    if not teacher:
        return JsonResponse({'success': False, 'error': 'Profesor no encontrado'}, status=404)

    tc, created = TeacherCourse.objects.get_or_create(
        course=course,
        teacher=teacher,
        defaults={'role': role, 'assigned_by': request.user}
    )

    if not created:
        return JsonResponse({'success': False, 'error': 'El profesor ya está asignado a este curso'}, status=400)

    return JsonResponse({
        'success': True,
        'teacher': teacher.get_full_name() or teacher.email,
        'role': tc.get_role_display(),
    })


@login_required
@require_POST
def teacher_remove(request, pk):
    """Remover profesor asistente (no titular)."""
    tc = get_object_or_404(TeacherCourse, pk=pk)
    course = tc.course

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    if tc.role == TeacherCourse.Role.TITULAR:
        return JsonResponse({'success': False, 'error': 'No se puede remover al titular'}, status=400)

    teacher_name = tc.teacher.get_full_name() or tc.teacher.email
    tc.delete()

    return JsonResponse({'success': True, 'message': f'{teacher_name} removido del curso'})


@login_required
@require_POST
def teacher_role_update(request, pk):
    """Cambiar rol de profesor en curso."""
    tc = get_object_or_404(TeacherCourse, pk=pk)
    course = tc.course

    assignment = TeacherCourse.objects.filter(
        course=course, teacher=request.user, role=TeacherCourse.Role.TITULAR
    ).first()

    if not assignment and request.user.role != User.Role.PROGRAMMER:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    if tc.teacher == request.user:
        return JsonResponse({'success': False, 'error': 'No puedes cambiar tu propio rol'}, status=400)

    new_role = request.POST.get('role')
    if new_role not in TeacherCourse.Role.values:
        return JsonResponse({'success': False, 'error': 'Rol inválido'}, status=400)

    tc.role = new_role
    tc.save(update_fields=['role'])

    return JsonResponse({
        'success': True,
        'role': tc.get_role_display(),
    })


# === ALIASES PARA URLS ===

@login_required
@require_POST
def invite_code_close(request, pk):
    """Cerrar código de invitación (alias de toggle con action=close)."""
    return invite_code_toggle(request, pk)


@login_required
@require_POST
def invite_code_open(request, pk):
    """Abrir código de invitación (alias de toggle con action=open)."""
    return invite_code_toggle(request, pk)


# Nombres alternativos para URLs
teacher_add = teacher_assign
teacher_change_role = teacher_role_update

student_add = student_enroll_code
student_change_status = student_status_update
student_withdraw = student_remove


@login_required
@require_GET
def course_switch(request, pk):
    """Cambiar curso seleccionado en sesión (HTMX endpoint)."""
    # Verificar que el usuario tiene acceso al curso
    if request.user.role in [User.Role.TEACHER, User.Role.STAFF, User.Role.PROGRAMMER]:
        has_access = Course.objects.filter(
            teacher_assignments__teacher=request.user,
            pk=pk,
            status=Course.Status.ACTIVE
        ).exists()
    elif request.user.role == User.Role.STUDENT:
        has_access = StudentCourse.objects.filter(
            student=request.user,
            course_id=pk,
            status=StudentCourse.Status.ACTIVE
        ).exists()
    else:
        has_access = False

    if not has_access:
        return JsonResponse({'success': False, 'error': 'Sin acceso a este curso'}, status=403)

    request.session['selected_course'] = pk
    return JsonResponse({'success': True, 'redirect': reverse('course_detail', args=[pk])})


@login_required
def student_enroll_by_code(request, code):
    """Inscribir estudiante via URL pública /cursos/inscribirse/<code>/."""
    code_upper = code.upper()
    invite_code = CourseCode.objects.filter(code=code_upper).select_related('course').first()
    if not invite_code:
        messages.error(request, 'Código inválido o expirado')
        return redirect('register')
    if not invite_code.is_valid():
        messages.error(request, 'Código expirado o cerrado')
        return redirect('register')
    return redirect(reverse('register') + '?course_code=' + code_upper)