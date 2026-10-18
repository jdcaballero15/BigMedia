import json

import pytest
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona

MISSING = object()


def nuevo_cartel(client, *, formato=MISSING, zona=MISSING, **changes: object):
    if formato is MISSING:
        formato = Formato.objects.get(nombre="Séxtuples")
    if zona is MISSING:
        zona = Zona.objects.get(nombre="Ciudad")
    payload = {
        "formato": formato.pk if formato is not None else None,
        "zona": zona.pk if zona is not None else None,
        "direccion": "Av. San Martín 1234",
        "tarifa_lista": "150000.00",
    }
    payload.update(changes)
    return client.post(
        "/api/inventario/carteles/", data=json.dumps(payload), content_type="application/json"
    )


@pytest.mark.django_db
@pytest.mark.regla("RN-005")
def test_cartel_inherits_capacity_and_shows_readable_name(operativo_client):
    formato = Formato.objects.get(nombre="Séxtuples")
    formato.capacidad_predeterminada = 6
    formato.save()

    response = nuevo_cartel(operativo_client, formato=formato)

    assert response.status_code == 201
    assert response.json()["capacidad"] == 6
    assert response.json()["nombre_visible"] == "Av. San Martín 1234 · 6 slots"
    assert response.json()["estado_nombre"] == "Activo"
    assert Cartel.objects.get(pk=response.json()["id"]).capacidad == 6


@pytest.mark.django_db
def test_capacity_can_be_overridden_and_not_reset_when_format_changes(operativo_client):
    created = nuevo_cartel(operativo_client, capacidad=8)
    assert created.status_code == 201
    cartel_id = created.json()["id"]
    led = Formato.objects.get(nombre="LED")
    changed = operativo_client.patch(
        f"/api/inventario/carteles/{cartel_id}/",
        data=json.dumps({"formato": led.pk}),
        content_type="application/json",
    )
    assert changed.status_code == 200
    assert changed.json()["capacidad"] == 8


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"direccion": " "}, "direccion"),
        ({"formato": None}, "formato"),
        ({"zona": None}, "zona"),
        ({"capacidad": 0}, "capacidad"),
        ({"tarifa_lista": "-1.00"}, "tarifa_lista"),
    ],
)
def test_invalid_cartel_returns_field_error_without_creating(operativo_client, changes, field):
    response = nuevo_cartel(operativo_client, **changes)
    assert response.status_code == 400
    assert field in response.json()
    assert Cartel.objects.count() == 0


@pytest.mark.django_db
def test_inactive_catalogs_are_rejected_on_create_but_preserved_on_edit(operativo_client):
    created = nuevo_cartel(operativo_client)
    assert created.status_code == 201
    cartel_id = created.json()["id"]
    formato = Formato.objects.get(nombre="Séxtuples")
    formato.activo = False
    formato.save()

    rejected = nuevo_cartel(operativo_client)
    assert rejected.status_code == 400
    assert "formato" in rejected.json()

    changed = operativo_client.patch(
        f"/api/inventario/carteles/{cartel_id}/",
        data=json.dumps({"direccion": "Av. San Martín 1236"}),
        content_type="application/json",
    )
    assert changed.status_code == 200
    assert changed.json()["formato"] == formato.pk

    changed_with_unchanged_reference = operativo_client.patch(
        f"/api/inventario/carteles/{cartel_id}/",
        data=json.dumps({"formato": formato.pk, "direccion": "Av. San Martín 1238"}),
        content_type="application/json",
    )
    assert changed_with_unchanged_reference.status_code == 200


@pytest.mark.django_db
def test_filters_search_without_accents_and_excludes_bajas(operativo_client):
    ciudad = Zona.objects.get(nombre="Ciudad")
    maipu = Zona.objects.get(nombre="Maipú")
    sextuples = Formato.objects.get(nombre="Séxtuples")
    led = Formato.objects.get(nombre="LED")
    first = nuevo_cartel(operativo_client, formato=sextuples, zona=ciudad)
    second = nuevo_cartel(
        operativo_client, formato=led, zona=maipu, direccion="Av. Martín Fierro 25"
    )
    third = nuevo_cartel(
        operativo_client, formato=sextuples, zona=ciudad, direccion="Av. Rivadavia 10"
    )
    assert all(row.status_code == 201 for row in (first, second, third))
    baja = EstadoCartel.objects.get(codigo="baja")
    operativo_client.patch(
        f"/api/inventario/carteles/{third.json()['id']}/",
        data=json.dumps({"estado": baja.pk}),
        content_type="application/json",
    )

    filtered = operativo_client.get(
        f"/api/inventario/carteles/?zona={ciudad.pk}&formato={sextuples.pk}&q=Martin"
    )
    assert [row["id"] for row in filtered.json()] == [first.json()["id"]]
    assert len(operativo_client.get("/api/inventario/carteles/").json()) == 2
    assert len(operativo_client.get("/api/inventario/carteles/?incluir_bajas=1").json()) == 3
    assert (
        operativo_client.get(f"/api/inventario/carteles/{third.json()['id']}/").status_code == 200
    )


@pytest.mark.django_db
def test_inactive_provider_zone_and_state_cannot_be_used_on_new_cartel(operativo_client):
    proveedor = Proveedor.objects.create(nombre="Tercero", activo=False)
    assert "proveedor" in nuevo_cartel(operativo_client, proveedor=proveedor.pk).json()

    zona = Zona.objects.get(nombre="Ciudad")
    zona.activo = False
    zona.save()
    assert "zona" in nuevo_cartel(operativo_client).json()

    zona.activo = True
    zona.save()
    estado = EstadoCartel.objects.get(codigo="mantenimiento")
    estado.activo = False
    estado.save()
    assert "estado" in nuevo_cartel(operativo_client, estado=estado.pk).json()


@pytest.mark.django_db
def test_inactive_default_state_is_rejected_on_create(operativo_client):
    activo = EstadoCartel.objects.get(codigo="activo")
    activo.activo = False
    activo.save()
    response = nuevo_cartel(operativo_client)
    assert response.status_code == 400
    assert "estado" in response.json()
    assert Cartel.objects.count() == 0


@pytest.mark.django_db
def test_cartel_can_be_marked_baja_but_never_deleted(operativo_client):
    created = nuevo_cartel(operativo_client)
    cartel_id = created.json()["id"]
    baja = EstadoCartel.objects.get(codigo="baja")
    changed = operativo_client.patch(
        f"/api/inventario/carteles/{cartel_id}/",
        data=json.dumps({"estado": baja.pk}),
        content_type="application/json",
    )
    assert changed.status_code == 200
    assert operativo_client.delete(f"/api/inventario/carteles/{cartel_id}/").status_code == 405
    assert Cartel.objects.filter(pk=cartel_id).exists()


@pytest.mark.django_db
def test_operativo_group_has_cartel_permissions(operativo_client):
    user = operativo_client.session.get("_auth_user_id")
    assert user is not None
    from django.contrib.auth import get_user_model

    operativo = get_user_model().objects.get(pk=user)
    assert operativo.has_perm("inventario.view_cartel")
    assert operativo.has_perm("inventario.add_cartel")
    assert operativo.has_perm("inventario.change_cartel")


@pytest.mark.django_db
def test_invalid_numeric_filter_returns_field_error(operativo_client):
    response = operativo_client.get("/api/inventario/carteles/?zona=no-existe")
    assert response.status_code == 400
    assert "zona" in response.json()
