"""Vistas de perfil: información del usuario, vinculación, GitHub, notificaciones y configuración.

- profile: muestra stats del perfil; estudiantes pueden vincularse con código.
- github_connect / github_disconnect: gestiona cuenta GitHub (solo programadores).
- notification_list: lista paginada de notificaciones.
- notification_read: marca notificación como leída (POST-only, CSRF).
- profile_edit: edición de nombre y apellido.
- avatar_upload: subida de foto de perfil.
- email_change / email_change_confirm: cambio de correo con confirmación.
- delete_account: baja de cuenta (GDPR).
- export_data: exportación de datos personales (GDPR).
- notification_preferences: preferencias de notificación por canal.
"""
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.http import url_has_allowed_host_and_scheme
from apps.accounts.models import User, Notification, NotificationPreferences, UserActivity
from apps.accounts.services import (
    get_user_stats, link_student_to_teacher,
    connect_github, disconnect_github, mark_notification_read,
    email_change_token, confirm_email_change,
    soft_delete_account, export_user_data,
)
from apps.accounts.forms import (
    ProfileEditForm, NotificationPreferencesForm, AvatarForm,
    EmailChangeForm, DeleteAccountForm,
)


@login_required
def profile(request):
    user = request.user

    if request.method == 'POST' and user.role == User.Role.STUDENT:
        code = request.POST.get('code', '')
        success, teacher = link_student_to_teacher(user, code)
        if success:
            messages.success(request, 'Vinculado a ' + (teacher.get_full_name() or teacher.email))
        else:
            messages.error(request, 'Código inválido')
        return redirect('profile')

    context = get_user_stats(user)
    context.update({
        'profile_form': ProfileEditForm(instance=user),
        'badges': user.badges,
        'streak': UserActivity.get_streak(user),
    })
    prefs, _ = NotificationPreferences.objects.get_or_create(user=user)
    context['prefs_form'] = NotificationPreferencesForm(instance=prefs)
    return render(request, 'accounts/profile.html', context)


@login_required
def github_connect(request):
    if request.user.role != User.Role.PROGRAMMER:
        messages.error(request, 'Solo programadores pueden conectar GitHub.')
        return redirect('profile')

    if request.method == 'POST':
        username = request.POST.get('github_username', '')
        token = request.POST.get('github_token', '')
        if connect_github(request.user, username, token):
            messages.success(request, f'Cuenta de GitHub @{username.strip()} conectada.')
        else:
            messages.error(request, 'Ingresá un nombre de usuario de GitHub.')
    return redirect('profile')


@login_required
def github_disconnect(request):
    if request.method != 'POST':
        return redirect('profile')
    disconnect_github(request.user)
    messages.success(request, 'Cuenta de GitHub desconectada.')
    return redirect('profile')


NOTIF_FIELDS = ['id', 'message', 'link', 'is_read', 'created_at']

@login_required
def notification_list(request):
    notifs = request.user.notifications.all().only(*NOTIF_FIELDS)
    notifs_page = Paginator(notifs, 20).get_page(request.GET.get('page'))
    return render(request, 'accounts/notification_list.html', {'notifications': notifs_page})


@login_required
def notification_read(request, pk):
    if request.method != 'POST':
        return redirect('notification_list')
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    mark_notification_read(notif)
    if notif.link and url_has_allowed_host_and_scheme(notif.link, allowed_hosts={request.get_host()}):
        return redirect(notif.link)
    return redirect('notification_list')


@login_required
def profile_edit(request):
    if request.method != 'POST':
        return redirect('profile')
    form = ProfileEditForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Datos actualizados.')
    else:
        messages.error(request, 'Revisá los datos ingresados.')
    return redirect('profile')


@login_required
def avatar_upload(request):
    if request.method != 'POST':
        return redirect('profile')
    form = AvatarForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Foto de perfil actualizada.')
    else:
        messages.error(request, 'No se pudo actualizar la foto de perfil.')
    return redirect('profile')


@login_required
def email_change(request):
    if request.method != 'POST':
        return redirect('profile')
    form = EmailChangeForm(request.POST, user=request.user)
    if form.is_valid():
        email = form.cleaned_data['email']
        request.user.pending_email = email
        request.user.save(update_fields=['pending_email'])
        link = request.build_absolute_uri(
            reverse('email_change_confirm', args=[email_change_token(request.user)])
        )
        body = render_to_string('registration/email_change_email.html', {
            'user': request.user,
            'link': link,
            'new_email': email,
        })
        send_mail(
            'Confirmá tu nuevo correo - StarStudy',
            body,
            None,
            [email],
            fail_silently=False,
        )
        messages.success(request, 'Te enviamos un enlace de confirmación a tu nuevo correo.')
    else:
        for error in form.non_field_errors():
            messages.error(request, error)
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
    return redirect('profile')


@login_required
def email_change_confirm(request, token):
    if confirm_email_change(request.user, token):
        messages.success(request, 'Correo actualizado correctamente.')
    else:
        messages.error(request, 'El enlace no es válido o expiró.')
    return redirect('profile')


@login_required
def delete_account(request):
    if request.method != 'POST':
        return redirect('profile')
    form = DeleteAccountForm(request.POST, user=request.user)
    if form.is_valid():
        soft_delete_account(request.user)
        auth_logout(request)
        messages.success(request, 'Tu cuenta fue eliminada. ¡Hasta pronto!')
        return redirect('login')
    messages.error(request, 'No se pudo eliminar la cuenta. Verificá la contraseña y la confirmación.')
    return redirect('profile')


@login_required
def export_data(request):
    payload = export_user_data(request.user)
    response = JsonResponse(payload, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="mis-datos.json"'
    return response


@login_required
def notification_preferences(request):
    if request.method != 'POST':
        return redirect('profile')
    prefs, _ = NotificationPreferences.objects.get_or_create(user=request.user)
    form = NotificationPreferencesForm(request.POST, instance=prefs)
    if form.is_valid():
        form.save()
        messages.success(request, 'Preferencias de notificación actualizadas.')
    else:
        messages.error(request, 'No se pudieron guardar las preferencias.')
    return redirect('profile')
