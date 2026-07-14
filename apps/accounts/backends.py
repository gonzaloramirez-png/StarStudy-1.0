"""Backend de autenticación personalizado: login por email + rol.

Permite que un mismo email tenga múltiples cuentas con diferentes roles.
El campo username del formulario se usa para el email.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import models


class EmailRoleBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, role=None, **kwargs):
        UserModel = get_user_model()

        if username is None or password is None:
            return None

        try:
            if role:
                user = UserModel.objects.get(email=username, role=role)
            else:
                # Sin rol: orden determinista por prioridad de rol
                role_priority = ['TEACHER', 'STAFF', 'PROGRAMMER', 'STUDENT']
                user = UserModel.objects.filter(email=username).order_by(
                    models.Case(*[models.When(role=r, then=pos) for pos, r in enumerate(role_priority)]),
                ).first()

            if user and user.check_password(password):
                return user

        except UserModel.DoesNotExist:
            return None

        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
