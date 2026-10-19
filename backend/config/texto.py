"""Utilidades de texto compartidas entre apps."""

import unicodedata


def normalizar_busqueda(value: str) -> str:
    """Pasa a minúsculas y quita tildes para buscar sin distinguirlas."""
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )
