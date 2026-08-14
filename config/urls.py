"""URLs principales de StarStudy.

Incluye: admin, accounts (home/profile/login/register), tasks, habits, schedule,
courses, gamification, dev y health check.
Sirve archivos media en desarrollo (DEBUG=True).
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import CustomHealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', CustomHealthCheckView.as_view(), name='health_check'),
    path('', include('apps.accounts.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('habitos/', include('apps.habits.urls')),
    path('schedule/', include('apps.schedule.urls')),
    path('cursos/', include('apps.courses.urls')),
    path('gamificacion/', include('apps.gamification.urls')),
    path('dev/', include('apps.dev.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
