"""Vistas de autenticación: registro, login, logout, cambio de contraseña y tutorial.

- register: formulario de registro con rol y código de vinculación opcional.
- join: redirige al registro prellenando el código desde URL pública /join/<code>/.
- logout_view: cierra sesión (requiere login).
- CustomPasswordChangeView: cambio de contraseña con formulario personalizado.
- dismiss_tutorial: descarta el onboarding del tutorial (POST-only, CSRF).
"""
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db import IntegrityError
from apps.accounts.models import User
from apps.accounts.forms import RegisterForm, CustomPasswordChangeForm


@login_required
def logout_view(request):
    if request.method != 'POST':
        return redirect('home')
    auth_logout(request)
    return redirect('login')


def register(request):
    initial_code = request.GET.get('code', '').strip().upper()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                code = form.cleaned_data.get('code', '').strip().upper()
                if code and user.role == User.Role.STUDENT:
                    teacher = User.objects.filter(code=code).exclude(role=User.Role.STUDENT).first()
                    if teacher:
                        user.linked_to = teacher
                        user.save(update_fields=['linked_to'])
                return redirect('login')
            except IntegrityError:
                messages.error(request, 'Error al registrar. Intentalo de nuevo.')
    else:
        form = RegisterForm(initial={'code': initial_code})

    return render(request, 'accounts/register.html', {'form': form})


def join(request, code):
    code_upper = code.upper()
    teacher = User.objects.filter(code=code_upper).exclude(role=User.Role.STUDENT).first()
    if not teacher:
        messages.error(request, 'Código inválido o expirado')
        return redirect('register')
    return redirect(reverse('register') + '?code=' + code_upper)


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.success(self.request, 'Contraseña actualizada.')
        return super().form_valid(form)


@login_required
def dismiss_tutorial(request):
    if request.method != 'POST':
        return redirect('home')
    request.session['onboarding_done'] = True
    request.session['show_tutorial'] = False
    return redirect(request.META.get('HTTP_REFERER', 'home'))
