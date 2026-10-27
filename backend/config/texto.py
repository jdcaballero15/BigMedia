"""Utilidades de texto compartidas entre apps."""

import unicodedata


def normalizar_busqueda(value: str) -> str:
    """Pasa a minúsculas y quita tildes para buscar sin distinguirlas."""
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )


def normalizar_comparacion(value: str) -> str:
    """Como `normalizar_busqueda`, y además cambia la puntuación por espacios y los colapsa."""
    sin_puntuacion = "".join(
        character if character.isalnum() else " " for character in normalizar_busqueda(value)
    )
    return " ".join(sin_puntuacion.split())


def distancia_edicion(a: str, b: str, tope: int) -> int:
    """Distancia de Levenshtein entre `a` y `b`; si supera `tope`, devuelve `tope + 1`."""
    if abs(len(a) - len(b)) > tope:
        return tope + 1
    anterior = list(range(len(b) + 1))
    for i, caracter_a in enumerate(a, start=1):
        actual = [i]
        for j, caracter_b in enumerate(b, start=1):
            costo = 0 if caracter_a == caracter_b else 1
            actual.append(min(anterior[j] + 1, actual[j - 1] + 1, anterior[j - 1] + costo))
        if min(actual) > tope:
            return tope + 1
        anterior = actual
    return min(anterior[-1], tope + 1)
