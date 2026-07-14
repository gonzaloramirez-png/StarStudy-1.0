"""Formularios de accounts: registro y login.

- RegisterForm: registro con email, rol, nombre, código de vinculación (opcional para estudiantes).
- CustomLoginForm: login con email + rol + contraseña. Valida que coincidan email, rol y password.
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db import transaction
from .models import User


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
        username = f"{base}_{role.lower()}"
        counter = 1
        while True:
            try:
                with transaction.atomic():
                    User.objects.select_for_update(nowait=True).filter(username=username).exists()
            except User.DoesNotExist:
                pass
            if not User.objects.filter(username=username).exists():
                return username
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
    username = forms.EmailField(label='Correo electrónico',
                                widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}))
    role = forms.ChoiceField(choices=User.Role.choices, label='Rol',
                             widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': '••••••••'})
        self.fields['role'].required = True

    def clean(self):
        role = self.cleaned_data.get('role')
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password and role:
            self.user_cache = authenticate(
                request=self.request,
                username=username,
                password=password,
                role=role,
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Correo, rol o contraseña incorrectos.',
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
