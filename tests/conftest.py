"""Configuración de pytest y fixtures compartidas."""
import pytest
from django.conf import settings


def pytest_configure(config):
    """Configuración inicial de Django para pytest."""
    if not settings.configured:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Configuración de BD para tests - usa SQLite en memoria."""
    with django_db_blocker.unblock():
        pass


@pytest.fixture
def user(db):
    """Usuario estudiante genérico."""
    from apps.accounts.tests import make_user
    return make_user()


@pytest.fixture
def teacher(db):
    """Usuario profesor genérico."""
    from apps.accounts.tests import make_user
    return make_user(role='TEACHER')


@pytest.fixture
def staff(db):
    """Usuario personal genérico."""
    from apps.accounts.tests import make_user
    return make_user(role='STAFF')


@pytest.fixture
def programmer(db):
    """Usuario programador genérico."""
    from apps.accounts.tests import make_user
    return make_user(role='PROGRAMMER')


@pytest.fixture
def authenticated_client(client, user):
    """Cliente autenticado como estudiante."""
    client.force_login(user)
    return client


@pytest.fixture
def teacher_client(client, teacher):
    """Cliente autenticado como profesor."""
    client.force_login(teacher)
    return client