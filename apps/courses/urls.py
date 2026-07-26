"""URLs de courses: gestión de cursos, códigos y asignaciones."""
from django.urls import path
from apps.courses import views
from apps.courses.views.bulk_ops import course_clone, bulk_task_assign

app_name = 'courses'

urlpatterns = [
    # Cursos
    path('', views.course_list, name='course_list'),
    path('nuevo/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/editar/', views.course_edit, name='course_edit'),
    path('<int:pk>/archivar/', views.course_archive, name='course_archive'),
    path('<int:pk>/eliminar/', views.course_delete, name='course_delete'),
    path('<int:pk>/clonar/', course_clone, name='course_clone'),

    # Código de invitación
    path('<int:pk>/codigo/regenerar/', views.invite_code_regenerate, name='invite_code_regenerate'),
    path('<int:pk>/codigo/cerrar/', views.invite_code_close, name='invite_code_close'),
    path('<int:pk>/codigo/abrir/', views.invite_code_open, name='invite_code_open'),

    # Cambiar curso seleccionado (HTMX)
    path('<int:pk>/cambiar/', views.course_switch, name='course_switch'),

    # Asignación profesores
    path('<int:pk>/profesor/agregar/', views.teacher_add, name='teacher_add'),
    path('profesor/<int:pk>/cambiar-rol/', views.teacher_change_role, name='teacher_change_role'),
    path('profesor/<int:pk>/remover/', views.teacher_remove, name='teacher_remove'),

    # Inscripción estudiantes
    path('<int:pk>/estudiante/agregar/', views.student_add, name='student_add'),
    path('estudiante/<int:pk>/cambiar-estado/', views.student_status_update, name='student_status_update'),
    path('estudiante/<int:pk>/retirar/', views.student_remove, name='student_remove'),
    path('inscribirse/<str:code>/', views.student_enroll_by_code, name='student_enroll_by_code'),

    # Asignación masiva
    path('<int:pk>/asignar-masivo/', bulk_task_assign, name='bulk_task_assign'),

    # Course switcher (HTMX)
    path('switch/', views.course_switch, name='course_switch'),
]