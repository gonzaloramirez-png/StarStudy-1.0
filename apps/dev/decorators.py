"""Decoradores de acceso para el módulo DEV."""
from functools import wraps
from django.http import JsonResponse
from .models import DevProfile


def programmer_required(view_func):
    """Garantiza que el usuario sea PROGRAMMER."""
    from apps.accounts.decorators import role_required
    return role_required('PROGRAMMER')(view_func)


def dev_profile_required(view_func):
    """Garantiza que el usuario tenga DevProfile. Lo crea si no existe."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile, _ = DevProfile.objects.get_or_create(user=request.user)
        request.dev_profile = profile
        return view_func(request, *args, **kwargs)
    return wrapper


def api_token_required(view_func):
    """Autenticación por token para la CLI. Acepta header Authorization: Token <token>."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return JsonResponse({'error': 'Token no proporcionado'}, status=401)
        token = auth_header.split(' ', 1)[1]
        try:
            profile = DevProfile.objects.select_related('user').get(api_token=token)
        except DevProfile.DoesNotExist:
            return JsonResponse({'error': 'Token inválido'}, status=401)
        request.dev_profile = profile
        request.user = profile.user
        return view_func(request, *args, **kwargs)
    return wrapper
