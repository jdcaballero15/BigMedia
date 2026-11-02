"""Importación del inventario desde CSV (HU-015). Las direcciones son ficticias."""

from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError
from django.test import Client

from apps.auditoria.models import RegistroAuditoria
from apps.inventario.models import Cartel, EstadoCartel, Formato, Proveedor, Zona

URL = "/api/inventario/importaciones/"
SEXTUPLES = "formato,direccion,slots,zona,proveedor,tarifa_lista,estado,foto_url,ref_origen,confirmar_distinto"
GRAN_FORMATO = "formato,direccion,tamano,zona,proveedor,tarifa_lista,estado,foto_url,ref_origen,confirmar_distinto"


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(username="admin", password="clave-segura-123")
    client = Client()
    client.force_login(user)
    return client


def _sextuples() -> Formato:
    return Formato.objects.get(nombre="Séxtuples")


def _gran_formato() -> Formato:
    return Formato.objects.get(nombre="Gran Formato")


def _importar(
    client: Client,
    filas: list[str],
    *,
    formato: Formato | None = None,
    encabezado: str = SEXTUPLES,
    simular: bool = False,
    contenido: bytes | None = None,
) -> Any:
    formato = formato or _sextuples()
    datos = contenido if contenido is not None else "\n".join([encabezado, *filas]).encode()
    archivo = SimpleUploadedFile("sextuples.csv", datos, content_type="text/csv")
    return client.post(
        URL,
        {"archivo": archivo, "formato": formato.pk, "simular": "1" if simular else "0"},
    )


def _filas(respuesta: Any, resultado: str) -> list[dict[str, Any]]:
    return [fila for fila in respuesta.json()["filas"] if fila["resultado"] == resultado]


def _cartel(direccion: str, *, slots: int = 6, zona: str = "Ciudad", **datos: Any) -> Cartel:
    datos.setdefault("estado", EstadoCartel.objects.get(codigo="activo"))
    return Cartel.objects.create(
        formato=_sextuples(),
        zona=Zona.objects.get(nombre=zona),
        direccion=direccion,
        capacidad=slots,
        **datos,
    )


@pytest.mark.django_db
@pytest.mark.regla("RN-005")
def test_importar_sextuples_valido_crea_carteles_con_capacidad_igual_a_slots(admin_client):
    respuesta = _importar(
        admin_client,
        [
            "Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,Sextuples fila 3,",
            "Séxtuples,Calle Inventada 200,4,Godoy Cruz,,,,,Sextuples fila 4,",
        ],
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["resumen"]["creadas"] == 2
    carteles = {c.direccion: c for c in Cartel.objects.select_related("zona", "estado")}
    assert carteles["Calle Ficticia 100"].capacidad == 6
    assert carteles["Calle Inventada 200"].capacidad == 4
    assert carteles["Calle Inventada 200"].zona.nombre == "Godoy Cruz"
    assert carteles["Calle Ficticia 100"].estado.codigo == "activo"


@pytest.mark.django_db
def test_importar_gran_formato_valido_crea_carteles_con_tamano_y_zona(admin_client):
    formato = _gran_formato()
    respuesta = _importar(
        admin_client,
        ["GRAN FORMATO,Ruta Ficticia km 5,6 X 3 m,Maipú,,150000,,https://fotos.example/1,GF 2,"],
        formato=formato,
        encabezado=GRAN_FORMATO,
    )

    assert respuesta.status_code == 200
    cartel = Cartel.objects.get()
    assert (cartel.tamano, cartel.zona.nombre) == ("6x3", "Maipú")
    assert cartel.capacidad == formato.capacidad_predeterminada
    assert cartel.tarifa_lista == Decimal("150000")
    assert cartel.foto_url == "https://fotos.example/1"


@pytest.mark.django_db
def test_importar_dos_veces_el_mismo_archivo_no_duplica(admin_client):
    filas = ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,"]
    _importar(admin_client, filas)

    respuesta = _importar(admin_client, filas)

    assert Cartel.objects.count() == 1
    assert respuesta.json()["resumen"]["omitidas"] == 1
    assert _filas(respuesta, "omitida")[0]["motivo"] == "Ya existe."


@pytest.mark.django_db
def test_importar_fila_invalida_la_rechaza_y_carga_las_demas(admin_client):
    respuesta = _importar(
        admin_client,
        [
            "Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,",
            "Séxtuples,Calle Inventada 200,6,Mendoza Norte,,-5,,ftp://foto,,",
        ],
    )

    assert Cartel.objects.count() == 1
    rechazos = {fila["campo"]: fila for fila in _filas(respuesta, "rechazada")}
    assert set(rechazos) == {"zona", "tarifa_lista", "foto_url"}
    assert all(fila["fila"] == 3 for fila in rechazos.values())
    assert respuesta.json()["resumen"]["rechazadas"] == 1


@pytest.mark.django_db
@pytest.mark.regla("RN-009")
def test_importar_fila_sin_zona_se_rechaza_con_el_campo(admin_client):
    respuesta = _importar(admin_client, ["Séxtuples,Calle Ficticia 100,6,,,,,,Sextuples fila 9,"])

    assert Cartel.objects.count() == 0
    [rechazo] = _filas(respuesta, "rechazada")
    assert (rechazo["campo"], rechazo["ref_origen"]) == ("zona", "Sextuples fila 9")
    assert rechazo["motivo"] == "Falta la zona."


@pytest.mark.django_db
def test_importar_fila_sin_obligatorios_lista_cada_campo(admin_client):
    respuesta = _importar(admin_client, [",,,,,,,,,"])

    campos = {fila["campo"] for fila in _filas(respuesta, "rechazada")}
    assert campos == {"formato", "direccion", "slots", "zona"}


@pytest.mark.django_db
@pytest.mark.regla("RN-008")
@pytest.mark.regla("RN-009")
def test_importar_zona_sin_tildes_ni_mayusculas_usa_la_de_la_lista(admin_client):
    _importar(admin_client, ["sextuples,  Calle   Ficticia 100 ,6,  MAIPU ,,,,,,"])

    cartel = Cartel.objects.get()
    assert (cartel.zona.nombre, cartel.direccion) == ("Maipú", "Calle Ficticia 100")


@pytest.mark.django_db
def test_importar_proveedor_y_estado_por_nombre_sin_distinguir_tildes(admin_client):
    Proveedor.objects.create(nombre="Proveedor Ficticio")
    _importar(
        admin_client,
        ["Séxtuples,Calle Ficticia 100,6,Ciudad,proveedor ficticio,,en mantenimiento,,,"],
    )

    cartel = Cartel.objects.select_related("proveedor", "estado").get()
    assert cartel.proveedor is not None
    assert cartel.proveedor.nombre == "Proveedor Ficticio"
    assert cartel.estado.codigo == "mantenimiento"


@pytest.mark.django_db
def test_importar_proveedor_o_estado_inexistente_rechaza_la_fila(admin_client):
    respuesta = _importar(admin_client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,Nadie,,Roto,,,"])

    assert Cartel.objects.count() == 0
    assert {fila["campo"] for fila in _filas(respuesta, "rechazada")} == {"proveedor", "estado"}


@pytest.mark.django_db
def test_importar_formato_distinto_del_elegido_rechaza_la_fila(admin_client):
    respuesta = _importar(admin_client, ["Banderolas,Calle Ficticia 100,6,Ciudad,,,,,,"])

    [rechazo] = _filas(respuesta, "rechazada")
    assert rechazo["campo"] == "formato"


@pytest.mark.django_db
def test_importar_marca_incompletas_las_que_no_tienen_opcionales(admin_client):
    respuesta = _importar(admin_client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,"])

    [creada] = _filas(respuesta, "creada")
    assert creada["motivo"] == "Incompleto: faltan proveedor, tarifa_lista, foto_url."
    assert respuesta.json()["resumen"]["incompletas"] == 1


@pytest.mark.django_db
def test_importar_archivo_con_columna_desconocida_se_rechaza_entero(admin_client):
    respuesta = _importar(
        admin_client,
        ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,,x"],
        encabezado=SEXTUPLES + ",color",
    )

    assert respuesta.status_code == 400
    assert "color" in respuesta.json()["archivo"][0]
    assert Cartel.objects.count() == 0


@pytest.mark.django_db
def test_importar_archivo_sin_una_columna_de_la_plantilla_se_rechaza(admin_client):
    respuesta = _importar(
        admin_client, ["Séxtuples,Calle Ficticia 100,Ciudad"], encabezado="formato,direccion,zona"
    )

    assert respuesta.status_code == 400
    assert "slots" in respuesta.json()["archivo"][0]


@pytest.mark.django_db
def test_importar_archivo_con_punto_y_coma_avisa_el_separador(admin_client):
    contenido = (SEXTUPLES.replace(",", ";") + "\nSéxtuples;Calle 1;6;Ciudad;;;;;;\n").encode()

    respuesta = _importar(admin_client, [], contenido=contenido)

    assert respuesta.status_code == 400
    assert "punto y coma" in respuesta.json()["archivo"][0]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "contenido",
    [b"", SEXTUPLES.encode(), "Séxtuples".encode("latin-1")],
    ids=["vacio", "sin-filas", "no-utf8"],
)
def test_importar_archivo_vacio_o_mal_codificado_se_rechaza(admin_client, contenido):
    respuesta = _importar(admin_client, [], contenido=contenido)

    assert respuesta.status_code == 400
    assert "archivo" in respuesta.json()


@pytest.mark.django_db
def test_importar_acepta_utf8_con_bom(admin_client):
    contenido = ("﻿" + SEXTUPLES + "\nSéxtuples,Calle Ficticia 100,6,Ciudad,,,,,,\n").encode()

    respuesta = _importar(admin_client, [], contenido=contenido)

    assert respuesta.status_code == 200
    assert Cartel.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("6x3", "6x3"), ("6 X 3", "6x3"), ("6x3 m", "6x3"), ("6\u00d73", "6x3"), ("4,5x2", "4.5x2")],
)
def test_importar_tamano_se_normaliza(admin_client, valor, esperado):
    _importar(
        admin_client,
        [f'Gran Formato,Ruta Ficticia km 5,"{valor}",Ciudad,,,,,,'],
        formato=_gran_formato(),
        encabezado=GRAN_FORMATO,
    )

    assert Cartel.objects.get().tamano == esperado


@pytest.mark.django_db
@pytest.mark.parametrize("valor", ["6", "seis por tres", "6x"])
def test_importar_tamano_invalido_se_rechaza(admin_client, valor):
    respuesta = _importar(
        admin_client,
        [f"Gran Formato,Ruta Ficticia km 5,{valor},Ciudad,,,,,,"],
        formato=_gran_formato(),
        encabezado=GRAN_FORMATO,
    )

    assert _filas(respuesta, "rechazada")[0]["campo"] == "tamano"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("valor", "valido"), [('"6,0"', True), ('"6,5"', False), ("0", False), ("x", False)]
)
def test_importar_slots_tiene_que_ser_entero_positivo(admin_client, valor, valido):
    respuesta = _importar(admin_client, [f"Séxtuples,Calle Ficticia 100,{valor},Ciudad,,,,,,"])

    assert Cartel.objects.count() == (1 if valido else 0)
    if not valido:
        assert _filas(respuesta, "rechazada")[0]["campo"] == "slots"


@pytest.mark.django_db
@pytest.mark.parametrize("direccion", ["ab", "x" * 201])
def test_importar_direccion_fuera_de_largo_se_rechaza(admin_client, direccion):
    respuesta = _importar(admin_client, [f"Séxtuples,{direccion},6,Ciudad,,,,,,"])

    assert _filas(respuesta, "rechazada")[0]["campo"] == "direccion"


@pytest.mark.django_db
def test_importar_tarifa_con_coma_decimal(admin_client):
    _importar(admin_client, ['Séxtuples,Calle Ficticia 100,6,Ciudad,,"1500,50",,,,'])

    assert Cartel.objects.get().tarifa_lista == Decimal("1500.50")


@pytest.mark.django_db
def test_importar_confirmar_distinto_invalido_se_rechaza(admin_client):
    respuesta = _importar(admin_client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,quizas"])

    assert _filas(respuesta, "rechazada")[0]["campo"] == "confirmar_distinto"


@pytest.mark.django_db
def test_importar_clave_exacta_existente_con_datos_distintos_se_rechaza(admin_client):
    _cartel("Calle Ficticia 100", tarifa_lista=Decimal("1000"))

    respuesta = _importar(admin_client, ["Séxtuples,calle ficticia 100.,6,Godoy Cruz,,2000,,,,"])

    [rechazo] = _filas(respuesta, "rechazada")
    assert rechazo["motivo"] == "Ya existe con datos distintos: zona, tarifa_lista."
    assert rechazo["cartel_coincidente"] == "Calle Ficticia 100 · 6 slots"
    assert Cartel.objects.count() == 1


@pytest.mark.django_db
def test_importar_coincide_con_cartel_de_baja_se_rechaza(admin_client):
    _cartel("Calle Ficticia 100", estado=EstadoCartel.objects.get(codigo="baja"))

    respuesta = _importar(admin_client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,"])

    assert _filas(respuesta, "rechazada")[0]["motivo"] == "Existe dado de baja."
    assert Cartel.objects.count() == 1


@pytest.mark.django_db
def test_importar_filas_repetidas_iguales_carga_la_primera(admin_client):
    respuesta = _importar(
        admin_client,
        [
            "Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,",
            "Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,",
        ],
    )

    assert Cartel.objects.count() == 1
    [rechazo] = _filas(respuesta, "rechazada")
    assert (rechazo["fila"], rechazo["motivo"]) == (3, "Fila repetida, igual a la fila 2.")


@pytest.mark.django_db
def test_importar_filas_repetidas_con_datos_distintos_rechaza_todas(admin_client):
    respuesta = _importar(
        admin_client,
        [
            "Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,",
            "Séxtuples,Calle Ficticia 100,6,Maipú,,,,,,",
        ],
    )

    assert Cartel.objects.count() == 0
    rechazos = _filas(respuesta, "rechazada")
    assert [fila["fila"] for fila in rechazos] == [2, 3]
    assert all(fila["motivo"] == "Conflicto entre las filas 2 y 3." for fila in rechazos)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "direccion",
    ["Av. Ficticia 100", "Avenida Ficticai 100", "Calle Uno y Calle Dos"],
    ids=["abreviatura", "tipeo", "interseccion"],
)
def test_importar_posible_duplicado_queda_en_revision(admin_client, direccion):
    _cartel("Avenida Ficticia 100")
    _cartel("Calle Dos y Calle Uno")

    respuesta = _importar(admin_client, [f"Séxtuples,{direccion},6,Ciudad,,,,,,"])

    [revision] = _filas(respuesta, "en_revision")
    assert revision["motivo"].startswith("Posible duplicado de ")
    assert Cartel.objects.count() == 2


@pytest.mark.django_db
def test_importar_misma_direccion_con_otros_slots_queda_en_revision(admin_client):
    _cartel("Calle Ficticia 100", slots=6)

    respuesta = _importar(admin_client, ["Séxtuples,Calle Ficticia 100,4,Ciudad,,,,,,"])

    [revision] = _filas(respuesta, "en_revision")
    assert revision["motivo"] == "Misma dirección con otros slots: Calle Ficticia 100 · 6 slots."


@pytest.mark.django_db
def test_importar_tamano_invertido_queda_en_revision(admin_client):
    formato = _gran_formato()
    _importar(
        admin_client,
        [
            "Gran Formato,Ruta Ficticia km 5,6x3,Ciudad,,,,,,",
            "Gran Formato,Ruta Ficticia km 5,3x6,Ciudad,,,,,,",
        ],
        formato=formato,
        encabezado=GRAN_FORMATO,
    )
    respuesta = _importar(
        admin_client,
        ["Gran Formato,Ruta Ficticia km 5,3x6,Ciudad,,,,,,"],
        formato=formato,
        encabezado=GRAN_FORMATO,
    )

    assert Cartel.objects.count() == 1
    assert _filas(respuesta, "en_revision")[0]["motivo"] == (
        "Tamaño invertido: Ruta Ficticia km 5 · 6x3."
    )


@pytest.mark.django_db
def test_importar_posible_duplicado_dentro_del_archivo_revisa_el_segundo(admin_client):
    respuesta = _importar(
        admin_client,
        [
            "Séxtuples,Avenida Ficticia 100,6,Ciudad,,,,,,",
            "Séxtuples,Av Ficticia 100,6,Ciudad,,,,,,",
        ],
    )

    assert Cartel.objects.count() == 1
    [revision] = _filas(respuesta, "en_revision")
    assert revision["fila"] == 3


@pytest.mark.django_db
def test_importar_posible_duplicado_con_confirmar_distinto_se_crea(admin_client):
    _cartel("Avenida Ficticia 100")

    respuesta = _importar(admin_client, ["Séxtuples,Av. Ficticia 100,6,Ciudad,,,,,,Sí"])

    assert Cartel.objects.count() == 2
    [creada] = _filas(respuesta, "creada")
    assert "Confirmado a mano como distinto de Avenida Ficticia 100 · 6 slots." in creada["motivo"]


@pytest.mark.django_db
def test_importar_confirmado_y_completo_solo_dice_que_se_confirmo(admin_client):
    Proveedor.objects.create(nombre="Proveedor Ficticio")
    _cartel("Avenida Ficticia 100")

    respuesta = _importar(
        admin_client,
        ["Séxtuples,Av Ficticia 100,6,Ciudad,Proveedor Ficticio,10,,https://fotos.example/2,,si"],
    )

    [creada] = _filas(respuesta, "creada")
    assert creada["motivo"] == "Confirmado a mano como distinto de Avenida Ficticia 100 · 6 slots."


@pytest.mark.django_db
def test_importar_confirmar_distinto_no_habilita_la_clave_exacta(admin_client):
    _cartel("Calle Ficticia 100", tarifa_lista=Decimal("1"))

    respuesta = _importar(admin_client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,,2,,,,si"])

    assert _filas(respuesta, "rechazada")[0]["motivo"].startswith("Ya existe con datos distintos")


@pytest.mark.django_db
def test_importar_simulado_no_guarda_nada(admin_client):
    respuesta = _importar(
        admin_client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,"], simular=True
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["simulado"] is True
    assert respuesta.json()["resumen"]["creadas"] == 1
    assert Cartel.objects.count() == 0
    assert RegistroAuditoria.objects.count() == 0


@pytest.mark.django_db
def test_importar_queda_auditado_con_origen_importacion(admin_client):
    _importar(admin_client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,Sextuples fila 3,"])

    cartel = Cartel.objects.get()
    registros = {
        r.campo: r for r in RegistroAuditoria.objects.filter(entidad="cartel", entidad_id=cartel.pk)
    }
    assert {"direccion", "capacidad", "zona", "importacion"} <= set(registros)
    assert registros["importacion"].valor_nuevo == "sextuples.csv (Sextuples fila 3)"
    assert all(r.origen == RegistroAuditoria.Origen.IMPORTACION for r in registros.values())
    assert registros["direccion"].usuario is not None


@pytest.mark.django_db
def test_importar_si_falla_el_guardado_de_una_fila_sigue_con_las_demas(admin_client):
    guardar = Cartel.save

    def falla_la_primera(self: Cartel, *args: Any, **kwargs: Any) -> None:
        if self.direccion == "Calle Ficticia 100":
            raise DatabaseError("falla")
        guardar(self, *args, **kwargs)

    with patch.object(Cartel, "save", falla_la_primera):
        respuesta = _importar(
            admin_client,
            [
                "Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,",
                "Séxtuples,Calle Inventada 200,6,Ciudad,,,,,,",
            ],
        )

    assert list(Cartel.objects.values_list("direccion", flat=True)) == ["Calle Inventada 200"]
    assert _filas(respuesta, "rechazada")[0]["motivo"] == "No se pudo guardar el cartel."


@pytest.mark.django_db
def test_importar_formato_digital_o_inexistente_se_rechaza(admin_client):
    led = Formato.objects.get(nombre="LED")
    archivo = SimpleUploadedFile("led.csv", SEXTUPLES.encode(), content_type="text/csv")

    respuesta = admin_client.post(URL, {"archivo": archivo, "formato": led.pk})
    sin_formato = admin_client.post(URL, {"archivo": archivo, "formato": "999999"})

    assert respuesta.status_code == 400
    assert "formato" in respuesta.json()
    assert sin_formato.status_code == 400


@pytest.mark.django_db
def test_importar_sin_archivo_se_rechaza(admin_client):
    respuesta = admin_client.post(URL, {"formato": _sextuples().pk})

    assert respuesta.status_code == 400
    assert "archivo" in respuesta.json()


@pytest.mark.django_db
def test_importar_solo_administrador(operativo_client, lector_client):
    for client in (operativo_client, lector_client):
        assert _importar(client, ["Séxtuples,Calle Ficticia 100,6,Ciudad,,,,,,"]).status_code == 403
    assert Client().post(URL).status_code in (401, 403)
    assert Cartel.objects.count() == 0
