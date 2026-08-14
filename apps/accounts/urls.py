"""URLs de accounts: home, auth, perfil, GitHub, notificaciones, join, school admin, pomodoro, push."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomLoginForm
from .views.school_admin import school_dashboard, manage_teachers

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', authentication_form=CustomLoginForm), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Perfil
    path('profile/', views.profile, name='profile'),
    path('profile/editar/', views.profile_edit, name='profile_edit'),
    path('profile/avatar/', views.avatar_upload, name='avatar_upload'),
    path('profile/email/', views.email_change, name='email_change'),
    path('profile/email/confirmar/<str:token>/', views.email_change_confirm, name='email_change_confirm'),
    path('profile/exportar/', views.export_data, name='export_data'),
    path('profile/eliminar/', views.delete_account, name='delete_account'),
    path('profile/preferencias/', views.notification_preferences, name='notification_preferences'),
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),

    # GitHub
    path('github/connect/', views.github_connect, name='github_connect'),
    path('github/disconnect/', views.github_disconnect, name='github_disconnect'),

    # Notificaciones
    path('notificaciones/', views.notification_list, name='notification_list'),
    path('notificaciones/<int:pk>/leer/', views.notification_read, name='notification_read'),

    # Vinculación
    path('join/<str:code>/', views.join, name='join'),

    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Onboarding
    path('onboarding/dismiss/', views.dismiss_tutorial, name='dismiss_tutorial'),

    # Push
    path('api/push-status/', views.push_status, name='push_status'),
    path('service-worker.js', views.service_worker, name='service_worker'),

    # Pomodoro
    path('pomodoro/', views.pomodoro, name='pomodoro'),
    path('pomodoro/save/', views.pomodoro_save, name='pomodoro_save'),

    # School Admin
    path('escuela/', school_dashboard, name='school_dashboard'),
    path('escuela/profesores/', manage_teachers, name='manage_teachers'),
]
