"""Vistas de exportación: Excel/CSV + PDF para notas y reportes."""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from apps.tasks.models import Task
from apps.courses.models import Course, TeacherCourse, StudentCourse
from apps.accounts.models import User
from apps.accounts.decorators import role_required
from apps.tasks.services_export import export_grades_csv, export_grades_pdf, export_student_report_pdf


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def export_course_grades(request, course_pk, fmt='csv'):
    """Exportar todas las notas del curso a CSV o PDF."""
    course = get_object_or_404(Course, pk=course_pk)

    is_teacher = TeacherCourse.objects.filter(
        course=course, teacher=request.user,
        role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).exists()
    if not is_teacher and request.user.role != User.Role.PROGRAMMER:
        return HttpResponse('Sin permisos', status=403)

    tasks = Task.objects.filter(
        course=course,
        is_personal=False,
    ).select_related('assigned_to', 'assigned_by', 'corrected_by').order_by('assigned_to__email', '-deadline')

    if fmt == 'pdf':
        return export_grades_pdf(course, tasks)
    return export_grades_csv(course, tasks)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def export_student_report(request, course_pk, student_pk, fmt='pdf'):
    """Exportar reporte individual de estudiante."""
    course = get_object_or_404(Course, pk=course_pk)
    student = get_object_or_404(User, pk=student_pk)

    is_teacher = TeacherCourse.objects.filter(
        course=course, teacher=request.user,
        role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).exists()
    if not is_teacher and request.user.role != User.Role.PROGRAMMER:
        return HttpResponse('Sin permisos', status=403)

    tasks = Task.objects.filter(
        course=course,
        assigned_to=student,
        is_personal=False,
    ).select_related('assigned_to', 'corrected_by').order_by('-deadline')

    if fmt == 'csv':
        return export_grades_csv(course, tasks)
    return export_student_report_pdf(course, student, tasks)
