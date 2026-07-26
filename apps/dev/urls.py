"""URLs del módulo DEV Workspace."""
from django.urls import path
from . import views

app_name = 'dev'

urlpatterns = [
    path('', views.dev_dashboard, name='dashboard'),

    path('challenges/', views.challenge_list, name='challenge_list'),
    path('challenges/create/', views.challenge_create, name='challenge_create'),
    path('challenges/<int:pk>/', views.challenge_detail, name='challenge_detail'),
    path('submissions/', views.submission_history, name='submission_history'),

    path('snippets/', views.snippet_list, name='snippet_list'),
    path('snippets/create/', views.snippet_create, name='snippet_create'),
    path('snippets/<int:pk>/edit/', views.snippet_edit, name='snippet_edit'),
    path('snippets/<int:pk>/delete/', views.snippet_delete, name='snippet_delete'),

    path('ranking/', views.dev_ranking, name='dev_ranking'),

    path('health/', views.health_dashboard, name='health_dashboard'),

    path('adr/', views.adr_list, name='adr_list'),
    path('adr/create/', views.adr_create, name='adr_create'),
    path('adr/<int:pk>/', views.adr_detail, name='adr_detail'),
    path('adr/<int:pk>/edit/', views.adr_edit, name='adr_edit'),

    # API endpoints para CLI
    path('api/health/ping/', views.api_health_ping, name='api_health_ping'),
    path('api/challenge/today/', views.api_challenge_today, name='api_challenge_today'),
    path('api/submit/', views.api_submit, name='api_submit'),
    path('api/snippets/', views.api_snippets, name='api_snippets'),
    path('api/snippet/', views.api_snippet_create, name='api_snippet_create'),
    path('api/profile/', views.api_profile, name='api_profile'),
]
