"""URLs de schedule: horarios, semáforo de riesgo, tutorías."""
from django.urls import path
from .views.schedule import (
    schedule_personal,
    schedule_course,
    risk_traffic_light,
    risk_update,
    risk_auto_calculate,
    tutoring_slots,
    tutoring_slot_delete,
    tutoring_appointments,
    tutoring_appointment_book,
    tutoring_appointment_confirm,
    tutoring_appointment_cancel_student,
)

urlpatterns = [
    # Horarios
    path('', schedule_personal, name='schedule_personal'),
    path('curso/<int:course_pk>/', schedule_course, name='schedule_course'),

    # Semáforo de riesgo
    path('curso/<int:course_pk>/riesgo/', risk_traffic_light, name='risk_traffic_light'),
    path('curso/<int:course_pk>/riesgo/<int:student_pk>/actualizar/', risk_update, name='risk_update'),
    path('curso/<int:course_pk>/riesgo/auto/', risk_auto_calculate, name='risk_auto_calculate'),

    # Tutorías - Slots (profesor)
    path('curso/<int:course_pk>/tutorias/', tutoring_slots, name='tutoring_slots'),
    path('tutorias/<int:slot_pk>/eliminar/', tutoring_slot_delete, name='tutoring_slot_delete'),

    # Tutorías - Citas (estudiante/profesor)
    path('curso/<int:course_pk>/citas/', tutoring_appointments, name='tutoring_appointments'),
    path('tutorias/<int:slot_pk>/reservar/', tutoring_appointment_book, name='tutoring_appointment_book'),
    path('citas/<int:appointment_pk>/confirmar/', tutoring_appointment_confirm, name='tutoring_appointment_confirm'),
    path('citas/<int:appointment_pk>/cancelar/', tutoring_appointment_cancel_student, name='tutoring_appointment_cancel_student'),
]