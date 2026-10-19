import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.clientes.models import Cliente, Marca, Rubro


@pytest.fixture
def superusuario_client(db):
    user = get_user_model().objects.create_superuser(username="adm", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("modelo", ["rubro", "cliente", "marca"])
def test_admin_de_clientes_lista_y_busca_cada_modelo_responde_200(superusuario_client, modelo):
    rubro = Rubro.objects.create(nombre="Bebidas")
    cliente = Cliente.objects.create(nombre="Agencia", razon_social="Agencia SA", tipo="directo")
    marca = Marca.objects.create(nombre="Marca", cliente=cliente, rubro=rubro)
    objetos = {"rubro": rubro, "cliente": cliente, "marca": marca}
    url = f"/admin/clientes/{modelo}/"

    assert superusuario_client.get(url).status_code == 200
    assert superusuario_client.get(url, {"q": "a"}).status_code == 200
    assert superusuario_client.get(f"{url}{objetos[modelo].pk}/change/").status_code == 200


@pytest.mark.django_db
def test_admin_de_clientes_borrar_cliente_esta_prohibido(superusuario_client):
    cliente = Cliente.objects.create(nombre="Agencia", razon_social="Agencia SA", tipo="directo")

    response = superusuario_client.get(f"/admin/clientes/cliente/{cliente.pk}/delete/")

    assert response.status_code == 403
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
