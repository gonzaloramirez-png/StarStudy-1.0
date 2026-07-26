"""URLs de accounts: home, auth, perfil, GitHub, notificaciones, join, school admin."""
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
    path('profile/', views.profile, name='profile'),
    path('github/connect/', views.github_connect, name='github_connect'),
    path('github/disconnect/', views.github_disconnect, name='github_disconnect'),
    path('notificaciones/', views.notification_list, name='notification_list'),
    path('notificaciones/<int:pk>/leer/', views.notification_read, name='notification_read'),
    path('join/<str:code>/', views.join, name='join'),

    # School Admin
    path('escuela/', school_dashboard, name='school_dashboard'),
    path('escuela/profesores/', manage_teachers, name='manage_teachers'),
]
