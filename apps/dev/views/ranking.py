"""Vista de ranking DEV global."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from ..decorators import dev_profile_required
from ..models import DevProfile


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def dev_ranking(request):
    """Ranking técnico global de desarrolladores."""
    profiles = DevProfile.objects.select_related('user').order_by('-total_dev_xp')[:50]

    current_profile = request.dev_profile
    my_position = None
    for i, p in enumerate(profiles, 1):
        if p.id == current_profile.id:
            my_position = i
            break

    if my_position is None:
        my_position = DevProfile.objects.filter(
            total_dev_xp__gt=current_profile.total_dev_xp
        ).count() + 1

    context = {
        'profiles': profiles,
        'my_position': my_position,
        'current_profile': current_profile,
    }
    return render(request, 'dev/ranking/dev_ranking.html', context)
