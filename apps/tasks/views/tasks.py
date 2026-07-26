"""Vistas de tasks: CRUD de tareas, comentarios, corrección y snippets.

- task_list: lista tareas con filtros, paginación (10 por página), unified para asignadas y personales.
- task_personal: atajo a task_list con is_personal=True.
- task_detail: detalle de tarea con comentarios paginados.
- task_create: crear tarea (asignada o personal) con rol TEACHER/STAFF/PROGRAMMER.
- task_complete: marcar tarea como completada (POST-only).
- task_delete: eliminar tarea creada por el usuario (POST-only).
- comment_create: agregar comentario a tarea (POST-only).
- task_correct: corregir/calificar tarea (profesor).
- task_return: devolver tarea al estudiante (profesor).
- snippet_list: lista de snippets del profesor.
- snippet_create: crear snippet.
- snippet_edit: editar snippet.
- snippet_delete: eliminar snippet.
- snippet_use: usar snippet en comentario (incrementa contador).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.tasks.models import Task, CommentSnippet
from apps.tasks.forms import TaskForm, CommentForm, CommentSnippetForm
from apps.tasks.services import (
    get_task_queryset, apply_filters, create_task,
    complete_task, delete_task, add_comment,
)
from apps.accounts.decorators import role_required


@login_required
def task_list(request, is_personal=False):
    user = request.user
    now = timezone.now()
    if not is_personal:
        is_personal = request.GET.get('personal') == '1'

    tasks = get_task_queryset(user, is_personal=is_personal)
    tasks = apply_filters(tasks, request.GET.get('importance'), request.GET.get('status'), now)

    paginator = Paginator(tasks, 10)
    tasks_page = paginator.get_page(request.GET.get('page'))

    context = {
        'tasks': tasks_page,
        'can_assign': user.role in ('TEACHER', 'STAFF', 'PROGRAMMER'),
        'now': now,
        'urgent_date': now + timedelta(days=3),
        'importance_choices': Task.Importance.choices,
        'status_choices': Task.Status.choices,
        'is_personal': is_personal,
        'user_role': user.role,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_personal(request):
    return task_list(request, is_personal=True)


@login_required
def task_detail(request, pk):
    user = request.user

    if user.role in ('TEACHER', 'STAFF', 'PROGRAMMER'):
        task = get_object_or_404(
            Task.objects.select_related('assigned_to', 'assigned_by', 'corrected_by'),
            pk=pk, assigned_by=user,
        )
    else:
        task = get_object_or_404(
            Task.objects.select_related('assigned_to', 'assigned_by', 'corrected_by'),
            pk=pk, assigned_to=user,
        )

    comments = task.comments.select_related('user').all()
    comments_page = Paginator(comments, 10).get_page(request.GET.get('comment_page'))

    # Snippets para el profesor
    snippets = []
    if user.role in ('TEACHER', 'STAFF', 'PROGRAMMER'):
        snippets = CommentSnippet.objects.filter(teacher=user).order_by('category', 'title')

    context = {
        'task': task,
        'can_assign': user.role in ('TEACHER', 'STAFF', 'PROGRAMMER'),
        'now': timezone.now(),
        'urgent_date': timezone.now() + timedelta(days=3),
        'user_role': user.role,
        'comments': comments_page,
        'form': CommentForm(),
        'snippets': snippets,
        'status_choices': Task.Status.choices,
    }
    return render(request, 'tasks/task_detail.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def task_create(request):
    personal = request.GET.get('personal') == '1'
    user = request.user

    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            task = create_task(form, user, is_personal=personal)
            return redirect('task_personal' if personal else 'task_detail', pk=task.pk)
    else:
        form = TaskForm(user=user)

    return render(request, 'tasks/task_form.html', {'form': form, 'is_personal': personal})


@login_required
def task_complete(request, pk):
    if request.method != 'POST':
        return redirect('task_list')

    task = get_object_or_404(Task, pk=pk)

    if task.assigned_to != request.user and task.assigned_by != request.user:
        messages.error(request, 'No tenés permiso para completar esta tarea.')
        return redirect('task_list')

    complete_task(task, request.user)
    return redirect('task_personal' if task.is_personal else 'task_list')


@login_required
def task_delete(request, pk):
    if request.method != 'POST':
        return redirect('task_list')

    task = get_object_or_404(Task, pk=pk, assigned_by=request.user)
    personal, _ = delete_task(task)
    return redirect('task_personal' if personal else 'task_list')


@login_required
def comment_create(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if task.assigned_to != request.user and task.assigned_by != request.user:
        messages.error(request, 'No tenés permiso para comentar en esta tarea.')
        return redirect('task_list')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            add_comment(task, request.user, form.cleaned_data['text'])

    return redirect('task_detail', pk=pk)


# === CORRECCIÓN Y CALIFICACIÓN (Profesor) ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def task_correct(request, pk):
    """Corregir/calificar una tarea."""
    task = get_object_or_404(Task, pk=pk, assigned_by=request.user)

    score = request.POST.get('score')
    comment = request.POST.get('comment', '').strip()

    try:
        score = int(score) if score else None
        if score is not None and (score < 0 or score > 100):
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Puntuación inválida (0-100)'}, status=400)

    task.mark_corrected(request.user, score=score)

    if comment:
        add_comment(task, request.user, comment)

    return JsonResponse({
        'success': True,
        'status': task.get_status_display(),
        'score': task.score,
        'corrected_at': task.corrected_at.strftime('%d/%m/%Y %H:%M') if task.corrected_at else None,
    })


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def task_return(request, pk):
    """Devolver tarea al estudiante para rehacer."""
    task = get_object_or_404(Task, pk=pk, assigned_by=request.user)
    comment = request.POST.get('comment', '').strip()

    task.mark_returned(request.user)

    if comment:
        add_comment(task, request.user, comment)

    return JsonResponse({
        'success': True,
        'status': task.get_status_display(),
    })


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def task_start_review(request, pk):
    """Marcar tarea como 'en revisión'."""
    task = get_object_or_404(Task, pk=pk, assigned_by=request.user)
    task.status = Task.Status.IN_REVIEW
    task.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'success': True, 'status': task.get_status_display()})


# === BANDEJA UNIFICADA DE CORRECCIÓN ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def correction_inbox(request):
    """Bandeja unificada de tareas para corregir."""
    user = request.user
    now = timezone.now()

    # Tareas entregadas pendientes de corrección
    pending = Task.objects.filter(
        assigned_by=user,
        is_personal=False,
        status__in=[Task.Status.PENDING, Task.Status.IN_REVIEW],
        is_completed=True
    ).select_related('assigned_to').order_by('completed_at')

    # Tareas en revisión
    in_review = Task.objects.filter(
        assigned_by=user,
        is_personal=False,
        status=Task.Status.IN_REVIEW
    ).select_related('assigned_to').order_by('-updated_at')

    # Tareas corregidas recientemente
    corrected = Task.objects.filter(
        assigned_by=user,
        is_personal=False,
        status=Task.Status.CORRECTED
    ).select_related('assigned_to', 'corrected_by').order_by('-corrected_at')[:20]

    context = {
        'pending': pending,
        'in_review': in_review,
        'corrected': corrected,
        'now': now,
    }
    return render(request, 'tasks/correction_inbox.html', context)


# === SNIPPETS (Banco de comentarios) ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def snippet_list(request):
    """Lista de snippets del profesor."""
    snippets = CommentSnippet.objects.filter(teacher=request.user).order_by('category', 'title')
    return render(request, 'tasks/snippet_list.html', {'snippets': snippets})


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def snippet_create(request):
    """Crear nuevo snippet."""
    if request.method == 'POST':
        form = CommentSnippetForm(request.POST)
        if form.is_valid():
            snippet = form.save(commit=False)
            snippet.teacher = request.user
            snippet.save()
            messages.success(request, 'Snippet creado.')
            return redirect('snippet_list')
    else:
        form = CommentSnippetForm()

    return render(request, 'tasks/snippet_form.html', {'form': form, 'action': 'Crear'})


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def snippet_edit(request, pk):
    """Editar snippet."""
    snippet = get_object_or_404(CommentSnippet, pk=pk, teacher=request.user)

    if request.method == 'POST':
        form = CommentSnippetForm(request.POST, instance=snippet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Snippet actualizado.')
            return redirect('snippet_list')
    else:
        form = CommentSnippetForm(instance=snippet)

    return render(request, 'tasks/snippet_form.html', {'form': form, 'action': 'Editar', 'snippet': snippet})


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def snippet_delete(request, pk):
    """Eliminar snippet."""
    snippet = get_object_or_404(CommentSnippet, pk=pk, teacher=request.user)
    snippet.delete()
    return JsonResponse({'success': True, 'message': 'Snippet eliminado'})


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def snippet_use(request, pk):
    """Usar snippet (incrementa contador y retorna contenido personalizado)."""
    snippet = get_object_or_404(CommentSnippet, pk=pk, teacher=request.user)
    student_name = request.POST.get('student_name', '').strip()

    content = snippet.content
    if student_name:
        content = content.replace('{student_name}', student_name)

    snippet.increment_usage()

    return JsonResponse({
        'success': True,
        'content': content,
        'title': snippet.title,
    })