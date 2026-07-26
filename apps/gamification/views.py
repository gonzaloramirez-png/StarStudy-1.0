"""Vistas de gamification: Quiz, Tip System, Rewards Store, Badges, Quick Quiz."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.models import User
from apps.courses.models import Course, TeacherCourse, StudentCourse
from apps.gamification.models import Quiz, QuizQuestion, QuizChoice, QuizAttempt, TipTransaction, Reward, Badge, StudentBadge
from apps.gamification.forms import QuizForm, QuizQuestionForm, TipForm, RewardForm, BadgeForm


# === QUIZ ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def quiz_list(request):
    """Lista de quizzes del profesor."""
    courses = TeacherCourse.objects.filter(teacher=request.user).select_related('course')
    quizzes = Quiz.objects.filter(created_by=request.user).select_related('course').order_by('-created_at')

    course_filter = request.GET.get('course')
    if course_filter:
        quizzes = quizzes.filter(course_id=course_filter)

    context = {
        'quizzes': quizzes,
        'courses': courses,
        'current_course': int(course_filter) if course_filter else None,
    }
    return render(request, 'gamification/quiz_list.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def quiz_create(request):
    """Crear nuevo quiz."""
    if request.method == 'POST':
        form = QuizForm(request.POST, user=request.user)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz creado. Ahora añade las preguntas.')
            return redirect('gamification:quiz_edit', pk=quiz.pk)
    else:
        form = QuizForm(user=request.user)

    return render(request, 'gamification/quiz_form.html', {'form': form, 'action': 'Crear'})


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def quiz_detail(request, pk):
    """Detalle del quiz con preguntas y estadísticas."""
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    questions = quiz.questions.all().order_by('order')
    attempts = quiz.attempts.select_related('student').order_by('-submitted_at')

    stats = attempts.aggregate(
        total=Count('id'),
        avg_score=Avg('score'),
        passed=Count('id', filter=Q(passed=True)),
    )

    context = {
        'quiz': quiz,
        'questions': questions,
        'attempts': attempts[:20],
        'stats': stats,
    }
    return render(request, 'gamification/quiz_detail.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def quiz_edit(request, pk):
    """Editar quiz y sus preguntas."""
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    questions = quiz.questions.all().order_by('order')

    if request.method == 'POST':
        if 'save_quiz' in request.POST:
            form = QuizForm(request.POST, instance=quiz, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Quiz actualizado.')
        elif 'add_question' in request.POST:
            q_form = QuizQuestionForm(request.POST)
            if q_form.is_valid():
                question = q_form.save(commit=False)
                question.quiz = quiz
                question.order = questions.count() + 1
                question.save()
                messages.success(request, 'Pregunta añadida.')
                return redirect('gamification:quiz_edit', pk=pk)

    form = QuizForm(instance=quiz, user=request.user)
    q_form = QuizQuestionForm()

    context = {
        'quiz': quiz,
        'form': form,
        'q_form': q_form,
        'questions': questions,
    }
    return render(request, 'gamification/quiz_form.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def quiz_delete(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    quiz.delete()
    messages.success(request, 'Quiz eliminado.')
    return redirect('gamification:quiz_list')


@login_required
def quiz_attempt(request, pk):
    """Estudiante realiza el quiz."""
    quiz = get_object_or_404(Quiz, pk=pk, is_active=True)

    # Verificar que el estudiante está en el curso
    if request.user.role != User.Role.STUDENT:
        messages.error(request, 'Solo los estudiantes pueden realizar quizzes.')
        return redirect('home')

    enrollment = StudentCourse.objects.filter(
        student=request.user,
        course=quiz.course,
        status=StudentCourse.Status.ACTIVE
    ).first()

    if not enrollment:
        messages.error(request, 'No estás inscrito en este curso.')
        return redirect('home')

    # Verificar intentos previos
    if quiz.max_attempts > 0:
        attempt_count = QuizAttempt.objects.filter(quiz=quiz, student=request.user).count()
        if attempt_count >= quiz.max_attempts:
            messages.error(request, 'Has agotado los intentos permitidos.')
            return redirect('gamification:quiz_results', pk=pk)

    # Verificar si ya hay un intento en progreso
    attempt = QuizAttempt.objects.filter(quiz=quiz, student=request.user, status='IN_PROGRESS').first()
    if not attempt:
        attempt = QuizAttempt.objects.create(quiz=quiz, student=request.user, status='IN_PROGRESS')

    if request.method == 'POST':
        answers = {}
        for question in quiz.questions.all():
            q_key = f'question_{question.pk}'
            answers[q_key] = request.POST.getlist(q_key)

        attempt.submit(answers)

        return redirect('gamification:quiz_results', pk=pk)

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'questions': quiz.questions.all().order_by('order'),
    }
    return render(request, 'gamification/quiz_attempt.html', context)


@login_required
def quiz_results(request, pk):
    """Resultados del quiz para el estudiante."""
    quiz = get_object_or_404(Quiz, pk=pk)
    attempts = QuizAttempt.objects.filter(quiz=quiz, student=request.user).order_by('-submitted_at')

    if not attempts.exists():
        messages.info(request, 'No has realizado este quiz aún.')
        return redirect('home')

    context = {
        'quiz': quiz,
        'attempts': attempts,
        'best_attempt': attempts.filter(passed=True).order_by('-score').first() or attempts.first(),
    }
    return render(request, 'gamification/quiz_results.html', context)


# === TIP SYSTEM ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def tip_list(request):
    """Lista de tips (bonus XP manuales) dados."""
    tips = TipTransaction.objects.filter(teacher=request.user).select_related('student', 'course').order_by('-created_at')

    context = {'tips': tips}
    return render(request, 'gamification/tip_list.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def tip_create(request):
    """Dar tip (+XP) a un estudiante."""
    form = TipForm(request.POST, user=request.user)
    if form.is_valid():
        tip = form.save(commit=False)
        tip.teacher = request.user
        tip.save()

        # Añadir XP al estudiante
        tip.student.add_xp(tip.xp_amount, source=f'Tip: {tip.reason}')

        # Notificar con link al loot box
        from apps.accounts.models import Notification
        Notification.objects.create(
            user=tip.student,
            message=f'¡Recibiste un tip de {tip.xp_amount} XP! Razón: {tip.get_reason_display()}',
            link=f'/tasks/lootbox/tip/{tip.pk}/'
        )

        return JsonResponse({
            'success': True,
            'message': f'¡{tip.xp_amount} XP otorgados a {tip.student.get_full_name()}!',
            'loot_box_url': f'/tasks/lootbox/tip/{tip.pk}/',
        })

    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# === REWARDS STORE ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def reward_list(request):
    """Tienda de recompensas del curso."""
    course_pk = request.GET.get('course')
    rewards = Reward.objects.filter(created_by=request.user)

    if course_pk:
        rewards = rewards.filter(course_id=course_pk)

    context = {
        'rewards': rewards.order_by('xp_cost'),
        'course_pk': int(course_pk) if course_pk else None,
    }
    return render(request, 'gamification/reward_list.html', context)


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def reward_create(request):
    """Crear recompensa."""
    if request.method == 'POST':
        form = RewardForm(request.POST, user=request.user)
        if form.is_valid():
            reward = form.save(commit=False)
            reward.created_by = request.user
            reward.save()
            messages.success(request, 'Recompensa creada.')
            return redirect('gamification:reward_list')
    else:
        form = RewardForm(user=request.user)

    return render(request, 'gamification/reward_form.html', {'form': form, 'action': 'Crear'})


@login_required
@require_POST
def reward_redeem(request, pk):
    """Estudiante canjea recompensa."""
    reward = get_object_or_404(Reward, pk=pk, is_active=True)
    student = request.user

    if student.role != User.Role.STUDENT:
        return JsonResponse({'success': False, 'error': 'Solo estudiantes'}, status=403)

    # Verificar inscripción
    enrollment = StudentCourse.objects.filter(
        student=student,
        course=reward.course,
        status=StudentCourse.Status.ACTIVE
    ).first()

    if not enrollment:
        return JsonResponse({'success': False, 'error': 'No estás en este curso'}, status=403)

    if student.xp < reward.xp_cost:
        return JsonResponse({'success': False, 'error': f'Necesitas {reward.xp_cost} XP, tienes {student.xp}'}, status=400)

    if reward.max_claims > 0 and reward.current_claims >= reward.max_claims:
        return JsonResponse({'success': False, 'error': 'Recompensa agotada'}, status=400)

    # Descontar XP
    student.xp -= reward.xp_cost
    student.level = (student.xp // 25) + 1
    student.save(update_fields=['xp', 'level'])

    # Registrar canje
    reward.current_claims += 1
    reward.save(update_fields=['current_claims'])

    # Notificar
    from apps.accounts.models import Notification
    Notification.objects.create(
        user=student,
        message=f'Canjeaste "{reward.name}" por {reward.xp_cost} XP.',
        link=f'/gamification/rewards/'
    )

    return JsonResponse({
        'success': True,
        'message': f'¡Canjeaste "{reward.name}"!',
        'new_xp': student.xp,
        'new_level': student.level,
    })


# === BADGES ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def badge_list(request):
    """Lista de badges creados."""
    badges = Badge.objects.filter(created_by=request.user).order_by('name')
    return render(request, 'gamification/badge_list.html', {'badges': badges})


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def badge_create(request):
    """Crear badge."""
    if request.method == 'POST':
        form = BadgeForm(request.POST, request.FILES)
        if form.is_valid():
            badge = form.save(commit=False)
            badge.created_by = request.user
            badge.save()
            messages.success(request, 'Badge creado.')
            return redirect('gamification:badge_list')
    else:
        form = BadgeForm()

    return render(request, 'gamification/badge_form.html', {'form': form, 'action': 'Crear'})


@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
@require_POST
def badge_award(request, pk):
    """Otorgar badge a estudiante."""
    badge = get_object_or_404(Badge, pk=pk, created_by=request.user)
    student_pk = request.POST.get('student_id')

    student = get_object_or_404(User, pk=student_pk, role=User.Role.STUDENT)

    # Verificar que el estudiante está en algún curso del profesor
    shared_courses = Course.objects.filter(
        teacher_assignments__teacher=request.user,
        student_enrollments__student=student,
        student_enrollments__status=StudentCourse.Status.ACTIVE
    ).distinct()

    if not shared_courses.exists():
        return JsonResponse({'success': False, 'error': 'El estudiante no está en tus cursos'}, status=403)

    # Otorgar badge (evitar duplicados)
    award, created = StudentBadge.objects.get_or_create(
        badge=badge,
        student=student,
        defaults={'earned_by': request.user}
    )

    if not created:
        return JsonResponse({'success': False, 'error': 'El estudiante ya tiene este badge'}, status=400)

    # XP extra por badge
    student.add_xp(badge.xp_reward, source=f'Badge: {badge.name}')

    # Notificar con link al loot box
    from apps.accounts.models import Notification
    Notification.objects.create(
        user=student,
        message=f'¡Obtuviste el badge "{badge.name}"! +{badge.xp_reward} XP',
        link=f'/tasks/lootbox/badge/{award.pk}/'
    )

    return JsonResponse({
        'success': True,
        'message': f'Badge "{badge.name}" otorgado a {student.get_full_name()}',
        'xp_reward': badge.xp_reward,
    })


# === MODO CLASE / PRESENTACIÓN ===

from django.db.models import Sum
from apps.tasks.models import Task
from apps.gamification.models import Ranking


@login_required
def presentation_mode(request, course_pk):
    """Modo presentación fullscreen para proyectar en clase."""
    course = get_object_or_404(Course, pk=course_pk)

    is_teacher = TeacherCourse.objects.filter(
        course=course, teacher=request.user,
        role__in=[TeacherCourse.Role.TITULAR, TeacherCourse.Role.ASISTENTE]
    ).exists()
    if not is_teacher and request.user.role != User.Role.PROGRAMMER:
        return render(request, '403.html', status=403)

    today = timezone.now().date()

    # Ranking semanal actual
    weekly_ranking = Ranking.objects.filter(
        course=course,
        period=Ranking.Period.WEEKLY,
        period_start__lte=today,
    ).select_related('student').order_by('position')[:10]

    # Si no hay ranking semanal, calcular en tiempo real
    if not weekly_ranking:
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())

        students_with_xp = []
        enrollments = course.student_enrollments.filter(status='ACTIVE').select_related('student')

        for enrollment in enrollments:
            student = enrollment.student
            xp_earned = Task.objects.filter(
                course=course,
                assigned_to=student,
                is_completed=True,
                completed_at__date__gte=week_start,
            ).aggregate(total=Sum('score'))['total'] or 0

            tasks_completed = Task.objects.filter(
                course=course,
                assigned_to=student,
                is_completed=True,
                completed_at__date__gte=week_start,
            ).count()

            if xp_earned > 0 or tasks_completed > 0:
                students_with_xp.append({
                    'student': student,
                    'xp_earned': xp_earned,
                    'total_xp': student.xp,
                    'tasks_completed': tasks_completed,
                })

        students_with_xp.sort(key=lambda x: x['xp_earned'], reverse=True)
        weekly_ranking = students_with_xp[:10]

    # Quizzes activos
    active_quizzes = Quiz.objects.filter(
        course=course,
        is_active=True,
    ).order_by('-created_at')[:3]

    # Recompensas disponibles
    available_rewards = Reward.objects.filter(
        course=course,
        is_active=True,
    ).order_by('xp_cost')[:5]

    # Estadísticas del curso
    stats = {
        'total_students': course.student_count,
        'tasks_this_week': Task.objects.filter(
            course=course,
            created_at__date__gte=today - timedelta(days=7),
        ).count(),
        'tasks_completed': Task.objects.filter(
            course=course,
            is_completed=True,
            completed_at__date=today,
        ).count(),
    }

    context = {
        'course': course,
        'weekly_ranking': weekly_ranking,
        'active_quizzes': active_quizzes,
        'available_rewards': available_rewards,
        'stats': stats,
        'is_weekly': True,
        'period_label': 'Semanal',
    }
    return render(request, 'gamification/presentation_mode.html', context)


# === QUIZ RÁPIDO MULTI-SECCIÓN ===

@role_required('TEACHER', 'STAFF', 'PROGRAMMER')
def quick_quiz_create(request):
    """Crear quiz rápido + asignar a múltiples secciones en 1 click.

    Flujo simplificado: título, XP, nota mínima, preguntas, asignar a cursos.
    """
    my_courses = Course.objects.filter(
        teacher_assignments__teacher=request.user,
        status=Course.Status.ACTIVE,
    ).order_by('name')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '')
        xp_reward = int(request.POST.get('xp_reward', 10))
        passing_score = int(request.POST.get('passing_score', 60))
        time_limit = int(request.POST.get('time_limit', 0))
        max_attempts = int(request.POST.get('max_attempts', 3))
        course_ids = request.POST.getlist('course_ids')

        if not title:
            messages.error(request, 'El título es obligatorio')
            return redirect('gamification:quick_quiz_create')

        if not course_ids:
            messages.error(request, 'Selecciona al menos un curso')
            return redirect('gamification:quick_quiz_create')

        # Recoger preguntas del formulario
        questions_data = []
        for i in range(1, 6):
            q_text = request.POST.get(f'q{i}_text', '').strip()
            if not q_text:
                continue

            q_type = request.POST.get(f'q{i}_type', 'SINGLE')
            q_points = int(request.POST.get(f'q{i}_points', 1))
            q_explanation = request.POST.get(f'q{i}_explanation', '')

            choices = []
            for j in range(1, 5):
                c_text = request.POST.get(f'q{i}_c{j}_text', '').strip()
                c_correct = request.POST.get(f'q{i}_c{j}_correct') == 'on'
                if c_text:
                    choices.append({'text': c_text, 'is_correct': c_correct})

            if choices:
                questions_data.append({
                    'text': q_text,
                    'type': q_type,
                    'points': q_points,
                    'explanation': q_explanation,
                    'choices': choices,
                })

        # Crear quiz en cada curso seleccionado
        created_quizzes = []
        for course_id in course_ids:
            course = get_object_or_404(Course, pk=course_id)

            quiz = Quiz.objects.create(
                course=course,
                title=title,
                description=description,
                xp_reward=xp_reward,
                passing_score=passing_score,
                time_limit=time_limit,
                max_attempts=max_attempts,
                created_by=request.user,
            )

            for qi, q_data in enumerate(questions_data, 1):
                question = QuizQuestion.objects.create(
                    quiz=quiz,
                    order=qi,
                    text=q_data['text'],
                    type=q_data['type'],
                    points=q_data['points'],
                    explanation=q_data['explanation'],
                )
                for ci, c_data in enumerate(q_data['choices'], 1):
                    QuizChoice.objects.create(
                        question=question,
                        order=ci,
                        text=c_data['text'],
                        is_correct=c_data['is_correct'],
                    )

            created_quizzes.append(quiz)

        count = len(created_quizzes)
        messages.success(request, f'Quiz "{title}" creado en {count} curso{"s" if count > 1 else ""}')
        return redirect('gamification:quiz_list')

    return render(request, 'gamification/quick_quiz_form.html', {'my_courses': my_courses})


# === RANKINGS ===

@login_required
def course_ranking(request, course_pk):
    """Ranking de estudiantes por curso con estadísticas de productividad."""
    from apps.gamification.models import Ranking

    course = get_object_or_404(Course, pk=course_pk)

    is_teacher = TeacherCourse.objects.filter(
        course=course, teacher=request.user
    ).exists()
    is_student = StudentCourse.objects.filter(
        student=request.user, course=course, status=StudentCourse.Status.ACTIVE
    ).exists()

    if not (is_teacher or is_student or request.user.role == User.Role.PROGRAMMER):
        messages.error(request, 'No tienes acceso a este curso.')
        return redirect('home')

    if is_teacher or request.user.role == User.Role.PROGRAMMER:
        Ranking.generate_weekly(course)
        Ranking.generate_monthly(course)

    weekly_rankings = Ranking.objects.filter(
        course=course, period=Ranking.Period.WEEKLY
    ).select_related('student').order_by('position')

    monthly_rankings = Ranking.objects.filter(
        course=course, period=Ranking.Period.MONTHLY
    ).select_related('student').order_by('position')

    stats = Ranking.get_course_stats(course)

    student_rank = None
    if is_student:
        student_rank = weekly_rankings.filter(student=request.user).first()

    context = {
        'course': course,
        'is_teacher': is_teacher,
        'is_student': is_student,
        'weekly_rankings': weekly_rankings,
        'monthly_rankings': monthly_rankings,
        'stats': stats,
        'student_rank': student_rank,
    }
    return render(request, 'gamification/course_ranking.html', context)


@login_required
def courses_ranking(request):
    """Ranking entre cursos: compara rendimiento promedio."""
    from apps.gamification.models import Ranking

    rankings = Ranking.get_all_courses_ranking()

    context = {
        'rankings': rankings,
    }
    return render(request, 'gamification/courses_ranking.html', context)