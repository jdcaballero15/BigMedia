"""Borrado de una carga errónea sin actividad desde el admin de Django (HU-006, criterio 4)."""

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.campanias.models import Campania
from apps.clientes.models import Cliente, Marca, Rubro
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona
from apps.reservas.models import Reserva


@pytest.fixture
def superusuario(db):
    return get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")


@pytest.fixture
def superusuario_client(superusuario):
    client = Client()
    client.force_login(superusuario)
    return client


def cartel() -> Cartel:
    return Cartel.objects.create(
        formato=Formato.objects.get(nombre="LED"),
        zona=Zona.objects.get(nombre="Ciudad"),
        estado=EstadoCartel.objects.get(codigo="activo"),
        direccion="Av. Errónea 123",
        capacidad=1,
        tarifa_lista="100.00",
    )


def borrar(client: Client, app: str, modelo: str, pk: int):
    return client.post(f"/admin/{app}/{modelo}/{pk}/delete/", {"post": "yes"})


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("app", "modelo", "entidad", "crear"),
    [
        ("inventario", "proveedor", "proveedor", lambda: Proveedor.objects.create(nombre="Error")),
        ("inventario", "zona", "zona", lambda: Zona.objects.create(nombre="Zona errónea")),
        ("inventario", "cartel", "cartel", cartel),
        ("clientes", "rubro", "rubro", lambda: Rubro.objects.create(nombre="Rubro erróneo")),
        ("clientes", "cliente", "cliente", lambda: Cliente.objects.create(nombre="Error")),
        ("campanias", "campania", "campania", lambda: Campania.objects.create(nombre="Error")),
    ],
)
def test_admin_borra_carga_sin_actividad_la_audita(
    superusuario_client, superusuario, app, modelo, entidad, crear
):
    objeto = crear()

    respuesta = borrar(superusuario_client, app, modelo, objeto.pk)

    assert respuesta.status_code == 302
    assert not type(objeto).objects.filter(pk=objeto.pk).exists()
    registros = RegistroAuditoria.objects.filter(entidad=entidad, entidad_id=objeto.pk)
    eliminado = registros.get(campo="eliminado")
    assert (eliminado.valor_anterior, eliminado.valor_nuevo) == ("", "si")
    assert eliminado.usuario == superusuario


@pytest.mark.django_db
def test_admin_borra_cartel_audita_sus_valores_anteriores(superusuario_client):
    objeto = cartel()

    borrar(superusuario_client, "inventario", "cartel", objeto.pk)

    valores = dict(
        RegistroAuditoria.objects.filter(entidad="cartel", entidad_id=objeto.pk).values_list(
            "campo", "valor_anterior"
        )
    )
    assert valores["direccion"] == "Av. Errónea 123"
    assert valores["tarifa_lista"] == "100.00"
    assert valores["zona"] == str(objeto.zona_id)
    assert RegistroAuditoria.objects.get(entidad_id=objeto.pk, campo="direccion").valor_nuevo == ""


@pytest.mark.django_db
def test_admin_borra_cartel_con_reservas_lo_rechaza(superusuario_client):
    objeto = cartel()
    Reserva(
        campania=Campania.objects.create(),
        cartel=objeto,
        fecha_inicio=date(2026, 11, 1),
        fecha_fin=date(2026, 11, 30),
    ).save()

    borrar(superusuario_client, "inventario", "cartel", objeto.pk)

    assert Cartel.objects.filter(pk=objeto.pk).exists()
    assert not RegistroAuditoria.objects.filter(entidad="cartel", campo="eliminado").exists()


@pytest.mark.django_db
def test_admin_borra_cliente_con_marcas_lo_rechaza(superusuario_client):
    cliente = Cliente.objects.create(nombre="Agencia")
    Marca.objects.create(nombre="Marca", cliente=cliente)

    borrar(superusuario_client, "clientes", "cliente", cliente.pk)

    assert Cliente.objects.filter(pk=cliente.pk).exists()
    assert not RegistroAuditoria.objects.filter(entidad="cliente").exists()


@pytest.mark.django_db
def test_admin_borrado_masivo_audita_cada_registro(superusuario_client):
    zonas = [Zona.objects.create(nombre=f"Zona errónea {n}") for n in (1, 2)]

    respuesta = superusuario_client.post(
        "/admin/inventario/zona/",
        {"action": "delete_selected", "_selected_action": [z.pk for z in zonas], "post": "yes"},
    )

    assert respuesta.status_code == 302
    assert not Zona.objects.filter(pk__in=[z.pk for z in zonas]).exists()
    auditadas = RegistroAuditoria.objects.filter(entidad="zona", campo="eliminado")
    assert sorted(auditadas.values_list("entidad_id", flat=True)) == sorted(z.pk for z in zonas)


@pytest.mark.django_db
def test_admin_staff_no_superusuario_no_borra(db):
    staff = get_user_model().objects.create_user(
        username="staff", password="clave-segura-123", is_staff=True
    )
    staff.user_permissions.add(
        *Permission.objects.filter(codename__in=["view_zona", "delete_zona"])
    )
    client = Client()
    client.force_login(staff)
    zona = Zona.objects.create(nombre="Zona errónea")

    respuesta = borrar(client, "inventario", "zona", zona.pk)

    assert respuesta.status_code == 403
    assert Zona.objects.filter(pk=zona.pk).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    ["/admin/inventario/cartel/add/", "/admin/campanias/campania/add/"],
)
def test_admin_de_inventario_y_campanias_no_permite_alta(superusuario_client, url):
    assert superusuario_client.get(url).status_code == 403


@pytest.mark.django_db
def test_admin_de_inventario_no_permite_editar(superusuario_client):
    objeto = cartel()

    superusuario_client.post(
        f"/admin/inventario/cartel/{objeto.pk}/change/", {"direccion": "Otra", "tarifa_lista": "1"}
    )

    objeto.refresh_from_db()
    assert objeto.direccion == "Av. Errónea 123"
