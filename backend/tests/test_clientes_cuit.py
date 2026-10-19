import pytest
from django.core.exceptions import ValidationError

from apps.clientes.validators import cuit_es_valido, normalizar_cuit, validar_cuit


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("20-12345678-6", "20123456786"),
        ("20123456786", "20123456786"),
        (" 30-71234567-1 ", "30712345671"),
    ],
)
def test_normalizar_cuit_con_o_sin_guiones_devuelve_once_digitos(valor, esperado):
    assert normalizar_cuit(valor) == esperado


@pytest.mark.parametrize(
    "valor", ["2012345678", "201234567861", "20-1234567-86", "2O123456786", "20 12345678 6", ""]
)
def test_normalizar_cuit_con_formato_invalido_lanza_error(valor):
    with pytest.raises(ValidationError):
        normalizar_cuit(valor)


@pytest.mark.parametrize("valor", ["20123456786", "30712345671", "23000000000", "27999999994"])
def test_cuit_es_valido_con_digito_correcto_devuelve_verdadero(valor):
    assert cuit_es_valido(valor) is True


@pytest.mark.parametrize(
    "valor",
    ["20123456789", "30712345670", "23000000001", "20000000010", "20000000011", "2012345678"],
)
def test_cuit_es_valido_con_digito_incorrecto_devuelve_falso(valor):
    assert cuit_es_valido(valor) is False


def test_validar_cuit_con_digito_incorrecto_lanza_error_en_castellano():
    with pytest.raises(ValidationError, match="dígito verificador"):
        validar_cuit("20123456789")


def test_validar_cuit_valido_o_vacio_no_lanza_error():
    validar_cuit("20123456786")
    validar_cuit("")
