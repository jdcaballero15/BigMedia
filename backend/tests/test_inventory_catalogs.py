import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.inventario.models import EstadoCartel, Formato, Proveedor, Zona


@pytest.mark.django_db
def test_seeded_zones_formats_and_states():
    assert set(Zona.objects.values_list("nombre", flat=True)) == {
        "Ciudad",
        "Godoy Cruz",
        "Maipú",
        "Luján de Cuyo",
        "Guaymallén",
        "Las Heras",
        "San Martín",
        "Rivadavia",
        "San Carlos",
    }
    assert Formato.objects.count() == 7
    assert Formato.objects.get(nombre="LED").modalidad == "digital"
    assert Formato.objects.get(nombre="Séxtuples").modalidad == "fija"
    assert set(EstadoCartel.objects.values_list("codigo", flat=True)) == {
        "activo",
        "mantenimiento",
        "baja",
        "apagado",
        "vidrio_destruido",
    }
    assert not Zona.objects.filter(nombre="Todos").exists()


@pytest.mark.django_db
def test_operativo_can_create_provider_and_inactivate_without_deleting(operativo_client):
    created = operativo_client.post(
        "/api/inventario/proveedores/",
        data=json.dumps({"nombre": "Proveedor Norte", "servicio": "Impresión"}),
        content_type="application/json",
    )
    assert created.status_code == 201
    provider_id = created.json()["id"]
    assert operativo_client.delete(f"/api/inventario/proveedores/{provider_id}/").status_code == 405

    changed = operativo_client.patch(
        f"/api/inventario/proveedores/{provider_id}/",
        data=json.dumps({"activo": False}),
        content_type="application/json",
    )
    assert changed.status_code == 200
    assert operativo_client.get("/api/inventario/proveedores/").json() == []
    assert len(operativo_client.get("/api/inventario/proveedores/?incluir_inactivos=1").json()) == 1
    assert Proveedor.objects.get(pk=provider_id).activo is False


@pytest.mark.django_db
def test_provider_name_is_required_and_unique_ignoring_case(operativo_client):
    first = operativo_client.post(
        "/api/inventario/proveedores/",
        data=json.dumps({"nombre": "Latcom"}),
        content_type="application/json",
    )
    duplicate = operativo_client.post(
        "/api/inventario/proveedores/",
        data=json.dumps({"nombre": "latcom"}),
        content_type="application/json",
    )
    blank = operativo_client.post(
        "/api/inventario/proveedores/",
        data=json.dumps({"nombre": "  "}),
        content_type="application/json",
    )
    assert first.status_code == 201
    assert duplicate.status_code == 400
    assert "nombre" in duplicate.json()
    assert blank.status_code == 400
    assert "nombre" in blank.json()
    assert Proveedor.objects.count() == 1


@pytest.mark.django_db
def test_format_capacity_must_be_positive(operativo_client):
    response = operativo_client.post(
        "/api/inventario/formatos/",
        data=json.dumps({"nombre": "Nuevo", "modalidad": "fija", "capacidad_predeterminada": 0}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "capacidad_predeterminada" in response.json()


@pytest.mark.django_db
def test_zone_can_be_created_and_inactive_formats_are_hidden(operativo_client):
    created = operativo_client.post(
        "/api/inventario/zonas/",
        data=json.dumps({"nombre": "Otra zona"}),
        content_type="application/json",
    )
    assert created.status_code == 201
    assert any(
        row["nombre"] == "Otra zona"
        for row in operativo_client.get("/api/inventario/zonas/").json()
    )

    formato = Formato.objects.get(nombre="LED")
    formato.activo = False
    formato.save()
    assert not any(
        row["nombre"] == "LED" for row in operativo_client.get("/api/inventario/formatos/").json()
    )
    assert any(
        row["nombre"] == "LED"
        for row in operativo_client.get("/api/inventario/formatos/?incluir_inactivos=1").json()
    )


@pytest.mark.django_db
def test_anonymous_and_unprivileged_users_cannot_write():
    payload = json.dumps({"nombre": "Sin permiso"})
    anonymous = Client().post(
        "/api/inventario/proveedores/", data=payload, content_type="application/json"
    )
    assert anonymous.status_code in (401, 403)

    user = get_user_model().objects.create_user(username="lectura", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    denied = client.post(
        "/api/inventario/proveedores/", data=payload, content_type="application/json"
    )
    assert denied.status_code == 403
    assert not Proveedor.objects.filter(nombre="Sin permiso").exists()


@pytest.mark.django_db
def test_operativo_write_without_csrf_is_rejected():
    from django.contrib.auth.models import Group

    user = get_user_model().objects.create_user(username="seba", password="clave-segura-123")
    user.groups.add(Group.objects.get(name="Operativo"))
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.post(
        "/api/inventario/proveedores/",
        data=json.dumps({"nombre": "No autorizado"}),
        content_type="application/json",
    )
    assert response.status_code == 403
    assert not Proveedor.objects.filter(nombre="No autorizado").exists()
