"""Vista dashboard principal del DEV Workspace."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from ..decorators import dev_profile_required
from ..models import DevChallenge, DevSubmission, DevSnippet, DevADR
from ..services import get_server_health


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def dev_dashboard(request):
    """Dashboard principal del DEV Workspace."""
    profile = request.dev_profile

    recent_submissions = DevSubmission.objects.filter(
        dev_profile=profile
    ).select_related('challenge')[:5]

    active_challenges = DevChallenge.objects.filter(is_active=True)[:3]

    recent_snippets = DevSnippet.objects.filter(
        dev_profile=profile
    )[:5]

    recent_adrs = DevADR.objects.all()[:3]

    health = get_server_health()

    context = {
        'profile': profile,
        'recent_submissions': recent_submissions,
        'active_challenges': active_challenges,
        'recent_snippets': recent_snippets,
        'recent_adrs': recent_adrs,
        'health': health,
    }
    return render(request, 'dev/dashboard.html', context)
