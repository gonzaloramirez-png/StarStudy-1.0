"""Endpoints API para la CLI 'starstudy dev'."""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from ..decorators import api_token_required
from ..models import DevChallenge, DevSubmission, DevSnippet, DevProfile
from ..services import evaluate_submission, get_server_health, record_ping


@csrf_exempt
@require_GET
@api_token_required
def api_health_ping(request):
    """GET /api/dev/health/ping — Health check / warm-up."""
    result = record_ping()
    health = get_server_health()
    return JsonResponse({
        'status': 'ok',
        'server': health,
        'ping': result,
    })


@csrf_exempt
@require_GET
@api_token_required
def api_challenge_today(request):
    """GET /api/dev/challenge/today — Devuelve el desafío activo más reciente."""
    challenge = DevChallenge.objects.filter(is_active=True).first()
    if not challenge:
        return JsonResponse({'error': 'No hay desafíos activos'}, status=404)

    profile = request.dev_profile
    submission = DevSubmission.objects.filter(
        dev_profile=profile, challenge=challenge
    ).first()

    return JsonResponse({
        'challenge': {
            'id': challenge.id,
            'title': challenge.title,
            'description': challenge.description,
            'difficulty': challenge.difficulty,
            'category': challenge.category,
            'initial_code': challenge.initial_code,
            'xp_reward': challenge.xp_reward,
        },
        'submitted': submission is not None,
        'result': {
            'status': submission.status,
            'xp_earned': submission.xp_earned,
        } if submission else None,
    })


@csrf_exempt
@require_POST
@api_token_required
def api_submit(request):
    """POST /api/dev/submit — Enviar solución a un desafío."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    challenge_id = data.get('challenge_id')
    code = data.get('code', '')

    if not challenge_id or not code:
        return JsonResponse({'error': 'challenge_id y code son requeridos'}, status=400)

    try:
        challenge = DevChallenge.objects.get(pk=challenge_id, is_active=True)
    except DevChallenge.DoesNotExist:
        return JsonResponse({'error': 'Desafío no encontrado'}, status=404)

    profile = request.dev_profile

    existing = DevSubmission.objects.filter(
        dev_profile=profile, challenge=challenge
    ).first()
    if existing:
        return JsonResponse({'error': 'Ya enviaste una solución para este desafío'}, status=409)

    submission = DevSubmission.objects.create(
        dev_profile=profile,
        challenge=challenge,
        submitted_code=code,
        status=DevSubmission.Status.ERROR,
    )
    evaluate_submission(submission)

    if submission.status == DevSubmission.Status.PASSED:
        profile.add_dev_xp(submission.xp_earned)

    return JsonResponse({
        'submission': {
            'id': submission.id,
            'status': submission.status,
            'xp_earned': submission.xp_earned,
            'execution_time_ms': submission.execution_time_ms,
        }
    })


@csrf_exempt
@require_GET
@api_token_required
def api_snippets(request):
    """GET /api/dev/snippets — Listar snippets del dev."""
    snippets = DevSnippet.objects.filter(
        dev_profile=request.dev_profile
    ).values('id', 'title', 'code', 'language', 'tags', 'created_at')

    return JsonResponse({'snippets': list(snippets)})


@csrf_exempt
@require_POST
@api_token_required
def api_snippet_create(request):
    """POST /api/dev/snippet — Crear un snippet."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    snippet = DevSnippet.objects.create(
        dev_profile=request.dev_profile,
        title=data.get('title', 'Sin título'),
        code=data.get('code', ''),
        language=data.get('language', 'python'),
        tags=data.get('tags', []),
        is_private=data.get('is_private', True),
    )

    return JsonResponse({
        'snippet': {
            'id': snippet.id,
            'title': snippet.title,
            'created_at': snippet.created_at.isoformat(),
        }
    }, status=201)


@csrf_exempt
@require_GET
@api_token_required
def api_profile(request):
    """GET /api/dev/profile — Perfil DEV del usuario."""
    profile = request.dev_profile
    return JsonResponse({
        'github_handle': profile.github_handle,
        'total_dev_xp': profile.total_dev_xp,
        'current_dev_level': profile.current_dev_level,
        'focus_mode_active': profile.focus_mode_active,
        'submissions_count': profile.submissions.count(),
        'snippets_count': profile.snippets.count(),
    })
