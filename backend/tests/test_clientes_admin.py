import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.clientes.models import Cliente, Contacto, Marca, Rubro


@pytest.fixture
def superusuario_client(db):
    user = get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("modelo", ["rubro", "cliente", "marca", "contacto"])
def test_admin_de_clientes_lista_y_busca_cada_modelo_responde_200(superusuario_client, modelo):
    rubro = Rubro.objects.create(nombre="Bebidas")
    cliente = Cliente.objects.create(nombre="Agencia", razon_social="Agencia SA", tipo="directo")
    marca = Marca.objects.create(nombre="Marca", cliente=cliente, rubro=rubro)
    contacto = Contacto.objects.create(nombre="Ana", cliente=cliente)
    objetos = {"rubro": rubro, "cliente": cliente, "marca": marca, "contacto": contacto}
    url = f"/admin/clientes/{modelo}/"

    assert superusuario_client.get(url).status_code == 200
    assert superusuario_client.get(url, {"q": "a"}).status_code == 200
    assert superusuario_client.get(f"{url}{objetos[modelo].pk}/change/").status_code == 200


@pytest.mark.django_db
def test_admin_de_clientes_borrar_cliente_con_marca_esta_protegido(superusuario_client):
    # HU-006 criterio 4: el superusuario borra solo una carga sin actividad (ver test_borrado_admin).
    cliente = Cliente.objects.create(nombre="Agencia", razon_social="Agencia SA", tipo="directo")
    Marca.objects.create(nombre="Agencia", cliente=cliente)

    superusuario_client.post(f"/admin/clientes/cliente/{cliente.pk}/delete/", {"post": "yes"})

    assert Cliente.objects.filter(pk=cliente.pk).exists()


@pytest.mark.django_db
def test_admin_de_clientes_alta_de_cliente_directo_crea_su_marca(superusuario_client):
    response = superusuario_client.post(
        "/admin/clientes/cliente/add/",
        {
            "nombre": "Bodega Admin",
            "razon_social": "Bodega Admin SA",
            "cuit": "",
            "tipo": "directo",
            "telefono": "",
            "correo": "",
            "activo": "on",
        },
    )

    assert response.status_code == 302
    cliente = Cliente.objects.get()
    assert list(cliente.marcas.values_list("nombre", flat=True)) == ["Bodega Admin"]
    superusuario_client.post(
        f"/admin/clientes/cliente/{cliente.pk}/change/",
        {
            "nombre": "Bodega Editada",
            "razon_social": "Bodega Admin SA",
            "cuit": "20123456786",
            "tipo": "directo",
            "telefono": "",
            "correo": "",
            "activo": "on",
        },
    )
    cliente.refresh_from_db()
    assert cliente.nombre == "Bodega Editada"
    assert cliente.cuit == "20123456786"
    assert Marca.objects.count() == 1


@pytest.mark.django_db
def test_admin_de_clientes_segundo_contacto_principal_se_rechaza(superusuario_client):
    # El admin valida la restricción: hay que desmarcar antes al principal (HU-068, criterio 3).
    cliente = Cliente.objects.create(nombre="Central", tipo="intermediario_formal")
    anterior = Contacto.objects.create(nombre="Ana", cliente=cliente, principal=True)
    response = superusuario_client.post(
        "/admin/clientes/contacto/add/",
        {
            "cliente": cliente.pk,
            "nombre": "Beto",
            "cargo": "",
            "correo": "",
            "telefono": "",
            "notas": "",
            "principal": "on",
            "activo": "on",
        },
    )
    assert response.status_code == 200
    assert "El cliente ya tiene un contacto principal." in response.content.decode()
    assert Contacto.objects.get(pk=anterior.pk).principal is True
    assert not Contacto.objects.filter(nombre="Beto").exists()
