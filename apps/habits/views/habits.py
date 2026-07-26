"""Vistas de habits: CRUD de hábitos diarios (solo STAFF).

- habito_list: lista hábitos con anotaciones (total_completions, completed_today) en 1 query.
- habito_toggle: marca/desmarca hábito (POST-only, no permite desmarcar).
- habito_create: formulario para crear hábito con título y horarios.
- habito_delete: elimina hábito (POST-only).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone
from apps.habits.models import Habit, HabitCompletion
from apps.habits.services import toggle_habit, create_habit, delete_habit
from apps.accounts.decorators import role_required


@role_required('STAFF', 'PROGRAMMER', 'STUDENT')
def habito_list(request):
    today = timezone.localdate()
    habits = request.user.habits.all().annotate(
        total_completions=Count('completions'),
        completed_today=Exists(
            HabitCompletion.objects.filter(
                habit_id=OuterRef('pk'),
                date=today,
            )
        ),
    )
    return render(request, 'habits/habito_list.html', {'habits': habits})


@role_required('STAFF', 'PROGRAMMER', 'STUDENT')
def habito_toggle(request, pk):
    if request.method != 'POST':
        return redirect('habito_list')

    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    created, habit = toggle_habit(habit)

    if not created:
        messages.error(request, f'No podés desmarcar "{habit.title}" hasta mañana.')
    else:
        messages.success(request, f'"{habit.title}" completado. ¡Subiste al nivel {habit.level}!')

    return redirect('habito_list')


@role_required('STAFF', 'PROGRAMMER', 'STUDENT')
def habito_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        start_time = request.POST.get('start_time', '').strip()
        end_time = request.POST.get('end_time', '').strip()
        if title and start_time and end_time:
            create_habit(request.user, title, start_time, end_time)
            messages.success(request, f'Hábito "{title}" creado.')
            return redirect('habito_list')
        else:
            messages.error(request, 'Completá todos los campos.')
    return render(request, 'habits/habito_form.html')


@role_required('STAFF', 'PROGRAMMER', 'STUDENT')
def habito_delete(request, pk):
    if request.method != 'POST':
        return redirect('habito_list')

    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    title = delete_habit(habit)
    messages.success(request, f'Hábito "{title}" eliminado.')
    return redirect('habito_list')
