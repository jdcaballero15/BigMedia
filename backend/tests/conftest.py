import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client


@pytest.fixture
def operativo_client(db):
    user = get_user_model().objects.create_user(
        username="operativo", password="clave-segura-123"
    )
    user.groups.add(Group.objects.get(name="Operativo"))
    client = Client()
    client.force_login(user)
    return client
