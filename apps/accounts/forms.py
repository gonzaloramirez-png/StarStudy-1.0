"""Formularios de accounts: registro, login, perfil y preferencias.

- RegisterForm: registro con email, rol, nombre, código de vinculación (opcional para estudiantes).
- CustomLoginForm: login con email + rol + contraseña. Valida que coincidan email, rol y password.
- ProfileEditForm: edición de nombre y apellido.
- AvatarForm: subida de foto de perfil con validación de tipo y tamaño.
- EmailChangeForm: solicitud de cambio de correo con contraseña.
- DeleteAccountForm: confirmación de baja de cuenta con contraseña.
- NotificationPreferencesForm: preferencias de notificación por canal.
- CustomPasswordChangeForm: cambio de contraseña con estilos de Bootstrap.
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.db import transaction
from .models import User, NotificationPreferences


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico',
                             widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}))
    role = forms.ChoiceField(choices=User.Role.choices, label='Rol',
                             widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_role'}))
    first_name = forms.CharField(required=True, label='Nombre',
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan'}))
    last_name = forms.CharField(required=True, label='Apellido',
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez'}))
    code = forms.CharField(required=False, label='Código del profesor (opcional)',
                           widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: A1B2C3', 'id': 'id_code'}))

    class Meta:
        model = User
        fields = ['email', 'role', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Repetí la contraseña'})

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        role = cleaned_data.get('role')
        code = cleaned_data.get('code', '').strip().upper()
        if code and role == User.Role.STUDENT:
            if not User.objects.filter(code=code).exclude(role=User.Role.STUDENT).exists():
                raise forms.ValidationError('El código de invitación no es válido o ha expirado.')
        if email and role:
            if User.objects.filter(email=email, role=role).exists():
                raise forms.ValidationError('Ya existe un usuario con ese correo y rol.')
            existing_roles = set(User.objects.filter(email=email).values_list('role', flat=True))
            if existing_roles and role not in existing_roles:
                raise forms.ValidationError(
                    'Este correo ya está registrado con otro rol. '
                    'Usá un correo diferente para cada rol.'
                )
        return cleaned_data

    def _generate_unique_username(self, base: str, role: str) -> str:
        """Genera username único de forma atómica dentro de transacción."""
        from django.db import OperationalError
        username = f"{base}_{role.lower()}"
        counter = 1
        while True:
            try:
                with transaction.atomic():
                    if not User.objects.select_for_update(nowait=True).filter(username=username).exists():
                        return username
            except OperationalError:
                pass
            username = f"{base}_{role.lower()}_{counter}"
            counter += 1

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._generate_unique_username(
            self.cleaned_data['email'].split('@')[0],
            self.cleaned_data.get('role', '')
        )
        if commit:
            with transaction.atomic():
                user.save()
                code = self.cleaned_data.get('code', '').strip().upper()
                if code and user.role == User.Role.STUDENT:
                    teacher = User.objects.filter(code=code).exclude(role=User.Role.STUDENT).first()
                    if teacher:
                        user.linked_to = teacher
                        user.save(update_fields=['linked_to'])
        return user


class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Correo electrónico',
                                widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': '••••••••'})

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(
                request=self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Correo o contraseña incorrectos.',
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
        }


class AvatarForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=True,
        label='Foto de perfil',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
    )

    class Meta:
        model = User
        fields = ['avatar']

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar
        if avatar.content_type not in ('image/jpeg', 'image/png', 'image/webp', 'image/gif'):
            raise forms.ValidationError('El archivo debe ser una imagen (JPG, PNG, WEBP o GIF).')
        if avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError('La imagen no puede superar los 2 MB.')
        return avatar


class EmailChangeForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label='Nuevo correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nuevo@correo.com'}),
    )
    password = forms.CharField(
        required=True,
        label='Tu contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError('La contraseña no es correcta.')
        return password

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if self.user and email == self.user.email.lower():
            raise forms.ValidationError('El nuevo correo debe ser distinto al actual.')
        if User.objects.filter(email=email, role=self.user.role).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo para tu rol.')
        return email


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        required=True,
        label='Tu contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    confirm = forms.BooleanField(
        required=True,
        label='Entiendo que esta acción es irreversible.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError('La contraseña no es correcta.')
        return password


class NotificationPreferencesForm(forms.ModelForm):
    email_deadlines = forms.BooleanField(
        required=False,
        label='Recordatorios de vencimiento por email',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    in_app = forms.BooleanField(
        required=False,
        label='Notificaciones in-app (vencimientos y hábitos)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    push = forms.BooleanField(
        required=False,
        label='Alertas push del navegador',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = NotificationPreferences
        fields = ['email_deadlines', 'in_app', 'push']


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
