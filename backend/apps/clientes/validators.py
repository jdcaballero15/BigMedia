"""Validación del CUIT de los clientes."""

import re

from django.core.exceptions import ValidationError

_FORMATO_CUIT = re.compile(r"[0-9]{11}|[0-9]{2}-[0-9]{8}-[0-9]")
_PESOS_CUIT = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def normalizar_cuit(valor: str) -> str:
    """Devuelve los 11 dígitos de un CUIT escrito con o sin guiones."""
    texto = valor.strip()
    if not _FORMATO_CUIT.fullmatch(texto):
        raise ValidationError(
            "Ingresá un CUIT de 11 dígitos, con o sin guiones (20-12345678-6).",
            code="formato",
        )
    return texto.replace("-", "")


def _son_once_digitos_ascii(valor: str) -> bool:
    return len(valor) == 11 and valor.isascii() and valor.isdigit()


def cuit_es_valido(digitos: str) -> bool:
    """Comprueba el dígito verificador con el algoritmo módulo 11 de AFIP."""
    if not _son_once_digitos_ascii(digitos):
        return False
    suma = sum(int(digito) * peso for digito, peso in zip(digitos[:10], _PESOS_CUIT, strict=True))
    verificador = 11 - suma % 11
    if verificador == 11:
        verificador = 0
    return verificador != 10 and verificador == int(digitos[10])


def validar_cuit(valor: str) -> None:
    """Validador del campo `Cliente.cuit`: vacío o 11 dígitos con verificador correcto."""
    if valor and not cuit_es_valido(valor):
        raise ValidationError("El CUIT no es válido: revisá el dígito verificador.", code="cuit")
