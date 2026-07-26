"""Vistas de desafíos de código."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from ..decorators import dev_profile_required
from ..models import DevChallenge, DevSubmission, DevProfile
from ..forms import DevSubmissionForm, DevChallengeForm
from ..services import evaluate_submission


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def challenge_list(request):
    """Listado de desafíos con filtros."""
    profile = request.dev_profile
    difficulty = request.GET.get('difficulty', '')
    category = request.GET.get('category', '')

    challenges = DevChallenge.objects.filter(is_active=True)
    if difficulty:
        challenges = challenges.filter(difficulty=difficulty)
    if category:
        challenges = challenges.filter(category=category)

    submissions = DevSubmission.objects.filter(dev_profile=profile)
    submitted_ids = set(submissions.values_list('challenge_id', flat=True))

    context = {
        'challenges': challenges,
        'submitted_ids': submitted_ids,
        'current_difficulty': difficulty,
        'current_category': category,
        'difficulty_choices': DevChallenge.Difficulty.choices,
        'category_choices': DevChallenge.Category.choices,
    }
    return render(request, 'dev/challenges/challenge_list.html', context)


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def challenge_detail(request, pk):
    """Detalle de un desafío y envío de solución."""
    profile = request.dev_profile
    challenge = get_object_or_404(DevChallenge, pk=pk, is_active=True)
    form = DevSubmissionForm()

    existing_submission = DevSubmission.objects.filter(
        dev_profile=profile, challenge=challenge
    ).first()

    if request.method == 'POST':
        form = DevSubmissionForm(request.POST)
        if form.is_valid():
            submission = DevSubmission.objects.create(
                dev_profile=profile,
                challenge=challenge,
                submitted_code=form.cleaned_data['submitted_code'],
                status=DevSubmission.Status.ERROR,
            )
            evaluate_submission(submission)

            if submission.status == DevSubmission.Status.PASSED:
                leveled_up = profile.add_dev_xp(submission.xp_earned)
                messages.success(request, f'¡Desafío resuelto! +{submission.xp_earned} DevXP')
                if leveled_up:
                    messages.success(request, f'¡Subiste a nivel {profile.current_dev_level}!')
            else:
                messages.warning(request, f'No pasó. Status: {submission.get_status_display()}')

            return redirect('dev:challenge_detail', pk=pk)

    context = {
        'challenge': challenge,
        'form': form,
        'existing_submission': existing_submission,
    }
    return render(request, 'dev/challenges/challenge_detail.html', context)


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def challenge_create(request):
    """Crear un nuevo desafío."""
    if request.method == 'POST':
        form = DevChallengeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Desafío creado.')
            return redirect('dev:challenge_list')
    else:
        form = DevChallengeForm()
    return render(request, 'dev/challenges/challenge_form.html', {'form': form, 'title': 'Nuevo Desafío'})


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def submission_history(request):
    """Historial de envíos del dev."""
    profile = request.dev_profile
    submissions = DevSubmission.objects.filter(
        dev_profile=profile
    ).select_related('challenge').order_by('-created_at')[:50]

    return render(request, 'dev/challenges/submission_history.html', {
        'submissions': submissions,
    })
