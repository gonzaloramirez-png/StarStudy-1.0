"""Vistas de schedule: horarios, semáforo de riesgo, tutorías.

- schedule_personal: horario personal del usuario (lectura/escritura).
- schedule_course: horario del curso del profesor (lectura/escritura).
- risk_traffic_light: semáforo de riesgo del curso (profesor).
- risk_update: actualizar nivel de riesgo (AJAX).
- tutoring_slots: gestión de slots de tutoría (profesor).
- tutoring_appointments: gestión de citas de tutoría (estudiante/profesor).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import Count, F
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.decorators import role_required
from apps.courses.models import Course, TeacherCourse, StudentCourse
from apps.schedule.models import ScheduleEntry, RiskTrafficLight, TutoringSlot, TutoringAppointment
from apps.schedule.forms import ScheduleEntryForm, RiskTrafficLightForm, TutoringSlotForm
from apps.schedule.services import get_schedule_context, add_schedule_entry, delete_schedule_entry


# === HORARIOS ===

@login_required
def schedule_personal(request):
    user = request.user

    if request.method == 'POST' and 'delete_id' in request.POST:
        delete_schedule_entry(request.POST['delete_id'], user)
        return redirect('schedule_personal')

    form = ScheduleEntryForm(request.POST or None, user=user)
    if request.method == 'POST' and 'add' in request.POST and form.is_valid():
        add_schedule_entry(user, form, ScheduleEntry.ScheduleType.PERSONAL)
        return redirect('schedule_personal')

    context = get_schedule_context(user, ScheduleEntry.ScheduleType.PERSONAL, 'Personal')
    context['form'] = form
    return render(request, 'schedule/schedule_personal.html', context)


@login_required
def schedule_course(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    user = request.user

    # Verificar acceso
    is_teacher = TeacherCourse.objects.filter(course=course, teacher=user).exists()
    is_student = StudentCourse.objects.filter(course=course, student=user, status=StudentCourse.Status.ACTIVE).exists()

    if not (is_teacher or is_student):
        messages.error(request, 'No tienes acceso a este horario.')
        return redirect('schedule_personal')

    readonly = not is_teacher

    if request.method == 'POST' and 'delete_id' in request.POST and not readonly:
        delete_schedule_entry(request.POST['delete_id'], user)
        return redirect('schedule_course', course_pk=course.pk)

    form = ScheduleEntryForm(request.POST or None, user=user)
    if request.method == 'POST' and 'add' in request.POST and form.is_valid() and not readonly:
        entry = form.save(commit=False)
        entry.user = user
        entry.schedule_type = ScheduleEntry.ScheduleType.COURSE
        entry.course = course
        entry.save()
        messages.success(request, 'Entrada añadida al horario del curso.')
        return redirect('schedule_course', course_pk=course.pk)

    # Obtener entradas del curso
    entries = ScheduleEntry.objects.filter(course=course).order_by('day', 'start_time')

    day_order = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    schedule = {day: [] for day in day_order}
    for entry in entries:
        schedule[entry.day].append(entry)

    day_labels = dict(ScheduleEntry.Day.choices)

    context = {
        'course': course,
        'schedule': schedule,
        'day_labels': day_labels,
        'form': form if not readonly else None,
        'readonly': readonly,
        'is_teacher': is_teacher,
        'page_title': f'Horario de "{course.name}"',
    }
    return render(request, 'schedule/schedule_course.html', context)


# === SEMÁFORO DE RIESGO ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def risk_traffic_light(request, course_pk):
    """Vista del semáforo de riesgo para un curso."""
    course = get_object_or_404(Course, pk=course_pk)

    # Verificar que es profesor del curso
    if not TeacherCourse.objects.filter(course=course, teacher=request.user).exists():
        messages.error(request, 'No tienes acceso a este curso.')
        return redirect('courses:course_list')

    # Obtener o crear semáforos para todos los estudiantes activos
    students = StudentCourse.objects.filter(
        course=course, status=StudentCourse.Status.ACTIVE
    ).select_related('student')

    # Crear semáforos faltantes
    for sc in students:
        RiskTrafficLight.objects.get_or_create(
            student=sc.student,
            course=course,
            defaults={'level': RiskTrafficLight.RiskLevel.GREEN}
        )

    risk_lights = RiskTrafficLight.objects.filter(course=course).select_related('student', 'updated_by')

    # Estadísticas
    stats = {
        'green': risk_lights.filter(level=RiskTrafficLight.RiskLevel.GREEN).count(),
        'yellow': risk_lights.filter(level=RiskTrafficLight.RiskLevel.YELLOW).count(),
        'red': risk_lights.filter(level=RiskTrafficLight.RiskLevel.RED).count(),
    }

    context = {
        'course': course,
        'risk_lights': risk_lights,
        'stats': stats,
        'risk_levels': RiskTrafficLight.RiskLevel.choices,
    }
    return render(request, 'schedule/risk_traffic_light.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def risk_update(request, course_pk, student_pk):
    """Actualizar nivel de riesgo de un estudiante (AJAX)."""
    course = get_object_or_404(Course, pk=course_pk)
    student = get_object_or_404(User, pk=student_pk)

    if not TeacherCourse.objects.filter(course=course, teacher=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    risk_light, _ = RiskTrafficLight.objects.get_or_create(
        student=student,
        course=course,
        defaults={'level': RiskTrafficLight.RiskLevel.GREEN}
    )

    new_level = request.POST.get('level')
    reasons = request.POST.get('reasons', '')

    if new_level not in RiskTrafficLight.RiskLevel.values:
        return JsonResponse({'success': False, 'error': 'Nivel inválido'}, status=400)

    risk_light.level = new_level
    risk_light.reasons = reasons
    risk_light.auto_calculated = False
    risk_light.updated_by = request.user
    risk_light.save()

    return JsonResponse({
        'success': True,
        'level': risk_light.get_level_display(),
        'badge_class': risk_light.get_badge_class(),
    })


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def risk_auto_calculate(request, course_pk):
    """Recalcular semáforos automáticamente basado en métricas."""
    course = get_object_or_404(Course, pk=course_pk)

    if not TeacherCourse.objects.filter(course=course, teacher=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

    students = StudentCourse.objects.filter(
        course=course, status=StudentCourse.Status.ACTIVE
    ).select_related('student')

    updated = 0
    for sc in students:
        student = sc.student

        # Métricas simples para cálculo automático
        from apps.tasks.models import Task
        now = timezone.now()

        overdue = Task.objects.filter(
            assigned_to=student,
            assigned_by__in=TeacherCourse.objects.filter(course=course).values('teacher'),
            is_completed=False,
            deadline__lt=now
        ).count()

        completed = Task.objects.filter(
            assigned_to=student,
            assigned_by__in=TeacherCourse.objects.filter(course=course).values('teacher'),
            is_completed=True
        ).count()

        pending = Task.objects.filter(
            assigned_to=student,
            assigned_by__in=TeacherCourse.objects.filter(course=course).values('teacher'),
            is_completed=False,
            deadline__gte=now
        ).count()

        # Lógica simple
        if overdue >= 3:
            level = RiskTrafficLight.RiskLevel.RED
        elif overdue >= 1 or (pending > 5 and completed == 0):
            level = RiskTrafficLight.RiskLevel.YELLOW
        else:
            level = RiskTrafficLight.RiskLevel.GREEN

        risk_light, _ = RiskTrafficLight.objects.get_or_create(
            student=student,
            course=course,
            defaults={'level': level}
        )

        if risk_light.auto_calculated or risk_light.level != level:
            risk_light.level = level
            risk_light.auto_calculated = True
            risk_light.reasons = f'Auto: {overdue} vencidas, {pending} pendientes, {completed} completadas'
            risk_light.updated_by = request.user
            risk_light.save()
            updated += 1

    return JsonResponse({'success': True, 'updated': updated})


# === TUTORÍAS ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def tutoring_slots(request, course_pk):
    """Gestión de slots de tutoría para un curso."""
    course = get_object_or_404(Course, pk=course_pk)

    if not TeacherCourse.objects.filter(course=course, teacher=request.user).exists():
        messages.error(request, 'No tienes acceso a este curso.')
        return redirect('courses:course_list')

    slots = TutoringSlot.objects.filter(course=course, teacher=request.user).order_by('day', 'start_time')

    if request.method == 'POST' and 'create' in request.POST:
        form = TutoringSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.teacher = request.user
            slot.course = course
            slot.save()
            messages.success(request, 'Slot de tutoría creado.')
            return redirect('tutoring_slots', course_pk=course.pk)
    else:
        form = TutoringSlotForm()

    context = {
        'course': course,
        'slots': slots,
        'form': form,
        'day_labels': dict(ScheduleEntry.Day.choices),
    }
    return render(request, 'schedule/tutoring_slots.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def tutoring_slot_delete(request, slot_pk):
    """Eliminar slot de tutoría."""
    slot = get_object_or_404(TutoringSlot, pk=slot_pk, teacher=request.user)
    course_pk = slot.course.pk
    slot.delete()
    messages.success(request, 'Slot eliminado.')
    return redirect('tutoring_slots', course_pk=course_pk)


@login_required
def tutoring_appointments(request, course_pk):
    """Citas de tutoría: lista para estudiante o gestión para profesor."""
    course = get_object_or_404(Course, pk=course_pk)
    user = request.user

    is_teacher = TeacherCourse.objects.filter(course=course, teacher=user).exists()
    is_student = StudentCourse.objects.filter(course=course, student=user, status=StudentCourse.Status.ACTIVE).exists()

    if not (is_teacher or is_student):
        messages.error(request, 'No tienes acceso.')
        return redirect('home')

    if is_teacher:
        # Profesor ve todas las citas
        appointments = TutoringAppointment.objects.filter(
            slot__course=course
        ).select_related('slot', 'student').order_by('-created_at')
    else:
        # Estudiante ve sus citas y slots disponibles
        appointments = TutoringAppointment.objects.filter(
            student=user, slot__course=course
        ).select_related('slot').order_by('-created_at')

    # Slots disponibles para reservar (solo estudiantes)
    available_slots = []
    if is_student:
        available_slots = TutoringSlot.objects.filter(
            course=course, is_active=True
        ).exclude(
            appointments__student=user
        ).annotate(
            booked=Count('appointments', filter=models.Q(appointments__status__in=[TutoringAppointment.Status.CONFIRMED, TutoringAppointment.Status.PENDING]))
        ).filter(
            booked__lt=models.F('max_students')
        ).order_by('day', 'start_time')

    context = {
        'course': course,
        'appointments': appointments,
        'available_slots': available_slots,
        'is_teacher': is_teacher,
        'is_student': is_student,
    }
    return render(request, 'schedule/tutoring_appointments.html', context)


@login_required
@require_POST
def tutoring_appointment_book(request, slot_pk):
    """Reservar cita de tutoría (estudiante)."""
    slot = get_object_or_404(TutoringSlot, pk=slot_pk, is_active=True)
    user = request.user

    if not StudentCourse.objects.filter(course=slot.course, student=user, status=StudentCourse.Status.ACTIVE).exists():
        return JsonResponse({'success': False, 'error': 'No estás inscrito en este curso'}, status=403)

    # Verificar disponibilidad
    booked = slot.appointments.filter(status__in=[TutoringAppointment.Status.CONFIRMED, TutoringAppointment.Status.PENDING]).count()
    if booked >= slot.max_students:
        return JsonResponse({'success': False, 'error': 'Slot lleno'}, status=400)

    # Verificar si ya tiene cita en este slot
    if slot.appointments.filter(student=user).exists():
        return JsonResponse({'success': False, 'error': 'Ya tienes una cita en este slot'}, status=400)

    appointment = TutoringAppointment.objects.create(
        slot=slot,
        student=user,
        status=TutoringAppointment.Status.PENDING,
        notes=request.POST.get('notes', '')
    )

    return JsonResponse({
        'success': True,
        'message': 'Cita solicitada. Pendiente de confirmación del profesor.',
        'appointment_id': appointment.pk,
    })


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def tutoring_appointment_confirm(request, appointment_pk):
    """Confirmar/cancelar cita (profesor)."""
    appointment = get_object_or_404(TutoringAppointment, pk=appointment_pk, slot__teacher=request.user)
    action = request.POST.get('action')

    if action == 'confirm':
        appointment.confirm()
        message = 'Cita confirmada'
    elif action == 'cancel':
        appointment.cancel()
        message = 'Cita cancelada'
    else:
        return JsonResponse({'success': False, 'error': 'Acción inválida'}, status=400)

    return JsonResponse({'success': True, 'message': message, 'status': appointment.get_status_display()})


@login_required
@require_POST
def tutoring_appointment_cancel_student(request, appointment_pk):
    """Cancelar propia cita (estudiante)."""
    appointment = get_object_or_404(TutoringAppointment, pk=appointment_pk, student=request.user)

    if appointment.status not in [TutoringAppointment.Status.PENDING, TutoringAppointment.Status.CONFIRMED]:
        return JsonResponse({'success': False, 'error': 'No se puede cancelar'}, status=400)

    appointment.cancel()
    return JsonResponse({'success': True, 'message': 'Cita cancelada'})