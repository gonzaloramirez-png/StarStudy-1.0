"""Vista de análisis de hábitos personal: métricas privadas de tasa de entregas y avance."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Avg, F
from django.utils import timezone
from datetime import timedelta

from apps.tasks.models import Task
from apps.habits.models import Habit, HabitCompletion
from apps.courses.models import StudentCourse


@login_required
def habit_analytics(request):
    """Panel de métricas personales de hábitos y entregas."""
    user = request.user
    today = timezone.now().date()
    now = timezone.now()

    # === TAREAS ===
    # Últimos 30 días
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)

    # Tareas asignadas (últimos 30 días)
    recent_tasks = Task.objects.filter(
        assigned_to=user,
        is_personal=False,
        created_at__date__gte=thirty_days_ago,
    )

    # Stats de tareas
    tasks_30d = recent_tasks.count()
    tasks_completed_30d = recent_tasks.filter(is_completed=True).count()
    tasks_overdue_30d = recent_tasks.filter(
        is_completed=False,
        deadline__date__lt=today,
    ).count()

    # Tasa de entrega (completadas / total)
    delivery_rate = round((tasks_completed_30d / tasks_30d * 100) if tasks_30d > 0 else 0, 1)

    # Tasa de puntualidad (completadas antes del deadline / total completadas)
    on_time = recent_tasks.filter(
        is_completed=True,
        completed_at__lte=F('deadline'),
    ).count() if tasks_completed_30d > 0 else 0
    on_time_rate = round((on_time / tasks_completed_30d * 100) if tasks_completed_30d > 0 else 0, 1)

    # Nota promedio
    avg_score = recent_tasks.filter(
        score__isnull=False,
    ).aggregate(avg=Avg('score'))['avg']
    avg_score = round(avg_score, 1) if avg_score else 0

    # XP ganado últimos 30 días
    xp_30d = recent_tasks.filter(
        is_completed=True,
        score__isnull=False,
    ).aggregate(total=Sum('score'))['total'] or 0

    # XP ganado última semana
    xp_7d = recent_tasks.filter(
        is_completed=True,
        score__isnull=False,
        completed_at__date__gte=seven_days_ago,
    ).aggregate(total=Sum('score'))['total'] or 0

    # === HÁBITOS ===
    user_habits = Habit.objects.filter(user=user).annotate(
        total_completions=Count('completions'),
    )

    habit_stats = []
    for habit in user_habits:
        completions_last_30 = habit.completions.filter(
            date__gte=thirty_days_ago,
        ).count()
        habit_stats.append({
            'habit': habit,
            'completions_last_30': completions_last_30,
            'rate': round((completions_last_30 / 30 * 100), 1) if completions_last_30 > 0 else 0,
        })

    # === CURSOS INSCRITOS ===
    enrolled_courses = StudentCourse.objects.filter(
        student=user,
        status=StudentCourse.Status.ACTIVE,
    ).select_related('course')

    # XP por curso
    course_xp = []
    for enrollment in enrolled_courses:
        course = enrollment.course
        xp = Task.objects.filter(
            course=course,
            assigned_to=user,
            is_completed=True,
            score__isnull=False,
        ).aggregate(total=Sum('score'))['total'] or 0
        course_xp.append({
            'course': course,
            'xp': xp,
            'level': user.level,
        })

    # === STREAKS ===
    # Racha actual de días con al menos 1 hábito completado
    streak = 0
    check_date = today
    while True:
        completed = HabitCompletion.objects.filter(
            habit__user=user,
            date=check_date,
        ).exists()
        if not completed:
            break
        streak += 1
        check_date -= timedelta(days=1)

    context = {
        'tasks_30d': tasks_30d,
        'tasks_completed_30d': tasks_completed_30d,
        'tasks_overdue_30d': tasks_overdue_30d,
        'delivery_rate': delivery_rate,
        'on_time_rate': on_time_rate,
        'avg_score': avg_score,
        'xp_30d': xp_30d,
        'xp_7d': xp_7d,
        'habit_stats': habit_stats,
        'course_xp': course_xp,
        'streak': streak,
        'total_habits': user_habits.count(),
        'today': today,
    }
    return render(request, 'habits/habit_analytics.html', context)
