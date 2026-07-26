"""URLs de tasks: lista, personal, crear, detalle, completar, eliminar, comentar, snippets."""
from django.urls import path
from .views.tasks import (
    task_list, task_personal, task_create, task_detail,
    task_complete, task_delete, comment_create,
    task_correct, task_return, task_start_review,
    correction_inbox,
    snippet_list, snippet_create, snippet_edit, snippet_delete, snippet_use,
)
from .views.grade_table import grade_table, grade_update, grade_bulk_update
from .views.export_views import export_course_grades, export_student_report
from .views.my_day import my_day

urlpatterns = [
    path('', task_list, name='task_list'),
    path('personal/', task_personal, name='task_personal'),
    path('mi-dia/', my_day, name='my_day'),
    path('create/', task_create, name='task_create'),
    path('<int:pk>/', task_detail, name='task_detail'),
    path('<int:pk>/complete/', task_complete, name='task_complete'),
    path('<int:pk>/delete/', task_delete, name='task_delete'),
    path('<int:pk>/comment/', comment_create, name='comment_create'),

    # Corrección/Calificación
    path('<int:pk>/correct/', task_correct, name='task_correct'),
    path('<int:pk>/return/', task_return, name='task_return'),
    path('<int:pk>/start-review/', task_start_review, name='task_start_review'),

    # Tabla de notas inline
    path('grade-table/<int:course_pk>/', grade_table, name='grade_table'),
    path('grade-update/<int:task_pk>/', grade_update, name='grade_update'),
    path('grade-bulk/<int:course_pk>/', grade_bulk_update, name='grade_bulk_update'),

    # Exportación
    path('export/<int:course_pk>/<str:fmt>/', export_course_grades, name='export_course_grades'),
    path('export/<int:course_pk>/student/<int:student_pk>/<str:fmt>/', export_student_report, name='export_student_report'),

    # Bandeja de corrección
    path('correction/', correction_inbox, name='correction_inbox'),

    # Snippets (Banco de comentarios)
    path('snippets/', snippet_list, name='snippet_list'),
    path('snippets/create/', snippet_create, name='snippet_create'),
    path('snippets/<int:pk>/edit/', snippet_edit, name='snippet_edit'),
    path('snippets/<int:pk>/delete/', snippet_delete, name='snippet_delete'),
    path('snippets/<int:pk>/use/', snippet_use, name='snippet_use'),
]