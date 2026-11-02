"""Importación del inventario desde CSV (HU-015).

La especificación está en docs/aidlc/inputs/importacion/README.md: plantillas, normalización,
duplicados y reporte. Cada fila válida se guarda por separado, así una que falla no frena a las
demás, y la simulación hace lo mismo sin guardar nada.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, TypeVar

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import URLValidator
from django.db import DatabaseError, models, transaction

from apps.auditoria import services as auditoria_services
from apps.auditoria.models import RegistroAuditoria
from config.texto import distancia_edicion, normalizar_comparacion

from .models import Cartel, EstadoCartel, Formato, Proveedor, Zona

CREADA = "creada"
OMITIDA = "omitida"
RECHAZADA = "rechazada"
EN_REVISION = "en_revision"

OPCIONALES = ("proveedor", "tarifa_lista", "estado", "foto_url", "ref_origen", "confirmar_distinto")
INCOMPLETOS = ("proveedor", "tarifa_lista", "foto_url")
ABREVIATURAS = {
    "av": "avenida",
    "gral": "general",
    "bv": "bulevar",
    "esq": "esquina",
    "pje": "pasaje",
}
SIGNOS_DIRECCION = str.maketrans(dict.fromkeys(".,;:#º°\"'«»“”", " "))
PATRON_TAMANO = re.compile(r"^(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)$")
DISTANCIA_MAXIMA = 2
LARGO_DIRECCION = (3, 200)
CAMPOS_COMPARADOS = ("zona", "proveedor", "estado", "tarifa_lista", "foto_url")
CAMPOS_AUDITADOS = (
    "formato",
    "direccion",
    "tamano",
    "capacidad",
    "zona",
    "proveedor",
    "estado",
    "tarifa_lista",
    "foto_url",
)

C = TypeVar("C", bound=models.Model)


@dataclass
class FilaReporte:
    fila: int
    ref_origen: str
    resultado: str
    campo: str = ""
    motivo: str = ""
    cartel_coincidente: str = ""


@dataclass
class Candidato:
    """Una fila ya validada, lista para comparar con el sistema y guardar."""

    fila: int
    ref_origen: str
    cartel: Cartel
    confirmar_distinto: bool
    clave: tuple[str, str]
    aproximada: str
    incompletos: list[str] = field(default_factory=list)
    confirmado_distinto_de: str = ""


@dataclass
class Resultado:
    simulado: bool
    filas: list[FilaReporte] = field(default_factory=list)

    def como_dict(self) -> dict[str, Any]:
        return {
            "simulado": self.simulado,
            "resumen": self.resumen(),
            "filas": [asdict(fila) for fila in self.filas],
        }

    def resumen(self) -> dict[str, int]:
        por_fila: dict[int, str] = {}
        for fila in self.filas:
            if por_fila.get(fila.fila) != RECHAZADA:
                por_fila[fila.fila] = fila.resultado
        resultados = list(por_fila.values())
        return {
            "leidas": len(resultados),
            "creadas": resultados.count(CREADA),
            "omitidas": resultados.count(OMITIDA),
            "rechazadas": resultados.count(RECHAZADA),
            "en_revision": resultados.count(EN_REVISION),
            "incompletas": sum(
                1 for f in self.filas if f.resultado == CREADA and "Incompleto" in f.motivo
            ),
        }


# --- Normalización ---


def limpiar(valor: str | None) -> str:
    """Saca los espacios de las puntas y deja uno solo entre palabras."""
    return " ".join((valor or "").split())


def clave_direccion(direccion: str) -> str:
    """Minúsculas, sin tildes (la ñ se conserva), sin signos y con un espacio entre palabras."""
    sin_tildes = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", direccion.casefold().replace("ñ", "\0"))
        if not unicodedata.combining(caracter)
    ).replace("\0", "ñ")
    return " ".join(sin_tildes.translate(SIGNOS_DIRECCION).split())


def clave_aproximada(direccion: str) -> str:
    """Expande abreviaturas y ordena las partes de una intersección («A y B» = «B y A»)."""
    palabras = [
        ABREVIATURAS.get(palabra, palabra) for palabra in clave_direccion(direccion).split()
    ]
    partes = re.split(r" (?:y|esquina) ", " ".join(palabras))
    return " y ".join(sorted(parte.strip() for parte in partes))


def normalizar_tamano(valor: str) -> str | None:
    """`6 X 3 m`, `6 por 3` con el signo de multiplicar o `6x3` quedan como `6x3`; `4,5x2`, como `4.5x2`. None si no es válido."""
    tamano = valor.casefold().replace("\u00d7", "x").replace(" ", "").replace(",", ".")
    tamano = tamano.removesuffix("m")
    return tamano if PATRON_TAMANO.match(tamano) else None


def _numero(valor: str) -> Decimal | None:
    try:
        numero = Decimal(valor.replace(",", "."))
    except InvalidOperation:
        return None
    return numero if numero.is_finite() else None


def es_sextuples(formato: Formato) -> bool:
    return normalizar_comparacion(formato.nombre) == "sextuples"


def _mismo_formato(escrito: str, formato: Formato) -> bool:
    """«PPL o Gran Formato» y «PPL/Gran Formato» son el mismo nombre."""

    def comparable(nombre: str) -> str:
        return normalizar_comparacion(nombre).replace(" o ", " ")

    return comparable(escrito) == comparable(formato.nombre)


def columnas_de(formato: Formato) -> list[str]:
    medida = "slots" if es_sextuples(formato) else "tamano"
    return ["formato", "direccion", medida, "zona", *OPCIONALES]


# --- Archivo ---


def _leer_filas(archivo: UploadedFile[bytes], formato: Formato) -> list[dict[str, str]]:
    """Valida codificación, separador y encabezado; devuelve las filas como diccionarios."""
    try:
        texto = archivo.read().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError(
            {"archivo": "El archivo no está en UTF-8. Guardalo como «CSV UTF-8»."}
        ) from error
    lineas = texto.splitlines()
    if not lineas or not lineas[0].strip():
        raise ValidationError({"archivo": "El archivo está vacío."})
    if ";" in lineas[0] and "," not in lineas[0]:
        raise ValidationError(
            {"archivo": "El archivo usa punto y coma como separador: guardalo separado por comas."}
        )
    lector = csv.DictReader(io.StringIO(texto))
    _validar_encabezado([limpiar(c).casefold() for c in lector.fieldnames or []], formato)
    lector.fieldnames = [limpiar(c).casefold() for c in lector.fieldnames or []]
    filas = [{clave: limpiar(valor) for clave, valor in fila.items()} for fila in lector]
    if not filas:
        raise ValidationError({"archivo": "El archivo no tiene filas de datos."})
    return filas


def _validar_encabezado(encabezado: list[str], formato: Formato) -> None:
    esperadas = columnas_de(formato)
    faltan = [columna for columna in esperadas if columna not in encabezado]
    sobran = [columna for columna in encabezado if columna not in esperadas]
    problemas = []
    if faltan:
        problemas.append("faltan las columnas " + ", ".join(faltan))
    if sobran:
        problemas.append("sobran las columnas " + ", ".join(sobran))
    if problemas:
        raise ValidationError(
            {"archivo": f"El encabezado no es el de la plantilla: {'; '.join(problemas)}."}
        )


# --- Fila por fila ---


class Catalogos:
    """Zonas, proveedores y estados activos, buscados sin distinguir mayúsculas ni tildes."""

    def __init__(self) -> None:
        self.zonas = self._por_nombre(Zona.objects.filter(activo=True))
        self.proveedores = self._por_nombre(Proveedor.objects.filter(activo=True))
        self.estados = self._por_nombre(EstadoCartel.objects.filter(activo=True))
        self.activo = EstadoCartel.objects.get(codigo="activo")

    @staticmethod
    def _por_nombre(queryset: models.QuerySet[C]) -> dict[str, C]:
        return {normalizar_comparacion(str(getattr(o, "nombre", ""))): o for o in queryset}


def _obligatorios(datos: dict[str, str], medida: str) -> list[tuple[str, str]]:
    nombres = {"formato": "el formato", "direccion": "la dirección", "zona": "la zona"}
    nombres[medida] = "el tamaño" if medida == "tamano" else "la cantidad de slots"
    return [(campo, f"Falta {texto}.") for campo, texto in nombres.items() if not datos.get(campo)]


def _medida(datos: dict[str, str], cartel: Cartel, formato: Formato) -> tuple[str, str] | None:
    """Pone el tamaño o los slots en el cartel; devuelve el error si el valor no sirve."""
    if not es_sextuples(formato):
        tamano = normalizar_tamano(datos["tamano"])
        if tamano is None:
            return ("tamano", "El tamaño tiene que ser ancho x alto, por ejemplo 6x3.")
        cartel.tamano = tamano
        cartel.capacidad = formato.capacidad_predeterminada
        return None
    slots = _numero(datos["slots"])
    if slots is None or slots != slots.to_integral_value() or slots < 1:
        return ("slots", "Los slots tienen que ser un número entero mayor o igual a 1.")
    cartel.capacidad = int(slots)
    return None


def _referencias(
    datos: dict[str, str], cartel: Cartel, catalogos: Catalogos
) -> list[tuple[str, str]]:
    errores = []
    zona = catalogos.zonas.get(normalizar_comparacion(datos["zona"]))
    if zona is None:
        errores.append(("zona", f"La zona «{datos['zona']}» no está en la lista."))
    else:
        cartel.zona = zona
    if datos.get("proveedor"):
        proveedor = catalogos.proveedores.get(normalizar_comparacion(datos["proveedor"]))
        if proveedor is None:
            errores.append(
                ("proveedor", f"El proveedor «{datos['proveedor']}» no existe o está inactivo.")
            )
        cartel.proveedor = proveedor
    estado = catalogos.estados.get(normalizar_comparacion(datos.get("estado") or "Activo"))
    if estado is None:
        errores.append(("estado", f"El estado «{datos['estado']}» no está en la lista."))
    else:
        cartel.estado = estado
    return errores


def _opcionales(datos: dict[str, str], cartel: Cartel) -> list[tuple[str, str]]:
    errores = []
    if datos.get("tarifa_lista"):
        tarifa = _numero(datos["tarifa_lista"])
        if tarifa is None or tarifa < 0:
            errores.append(("tarifa_lista", "La tarifa tiene que ser un número mayor o igual a 0."))
        else:
            cartel.tarifa_lista = tarifa
    if datos.get("foto_url"):
        try:
            URLValidator(schemes=["http", "https"])(datos["foto_url"])
        except ValidationError:
            errores.append(("foto_url", "La foto tiene que ser un enlace http o https."))
        else:
            cartel.foto_url = datos["foto_url"]
    if normalizar_comparacion(datos.get("confirmar_distinto", "")) not in ("", "si"):
        errores.append(("confirmar_distinto", "confirmar_distinto tiene que ser «si» o vacío."))
    return errores


def _validar_fila(
    numero: int, datos: dict[str, str], formato: Formato, catalogos: Catalogos
) -> Candidato | list[FilaReporte]:
    medida = "slots" if es_sextuples(formato) else "tamano"
    ref = datos.get("ref_origen", "")
    errores = _obligatorios(datos, medida)
    cartel = Cartel(formato=formato, direccion=datos.get("direccion", ""))
    if datos.get("formato") and not _mismo_formato(datos["formato"], formato):
        errores.append(("formato", f"El formato «{datos['formato']}» no es {formato.nombre}."))
    largo = len(cartel.direccion)
    if cartel.direccion and not LARGO_DIRECCION[0] <= largo <= LARGO_DIRECCION[1]:
        errores.append(("direccion", "La dirección tiene que tener entre 3 y 200 caracteres."))
    if datos.get(medida) and (error := _medida(datos, cartel, formato)):
        errores.append(error)
    if datos.get("zona"):
        errores.extend(_referencias(datos, cartel, catalogos))
    errores.extend(_opcionales(datos, cartel))
    if errores:
        return [FilaReporte(numero, ref, RECHAZADA, campo, motivo) for campo, motivo in errores]
    return Candidato(
        fila=numero,
        ref_origen=ref,
        cartel=cartel,
        confirmar_distinto=bool(datos.get("confirmar_distinto")),
        clave=(clave_direccion(cartel.direccion), _medida_texto(cartel)),
        aproximada=clave_aproximada(cartel.direccion),
        incompletos=[campo for campo in INCOMPLETOS if not datos.get(campo)],
    )


def _medida_texto(cartel: Cartel) -> str:
    return cartel.tamano if cartel.tamano else str(cartel.capacidad)


# --- Duplicados ---


def _datos(cartel: Cartel) -> dict[str, str]:
    valores = {
        "zona": cartel.zona_id,
        "proveedor": cartel.proveedor_id,
        "estado": cartel.estado_id,
        "tarifa_lista": cartel.tarifa_lista,
        "foto_url": cartel.foto_url or None,
    }
    return {campo: "" if valor is None else str(valor) for campo, valor in valores.items()}


def _distintos(a: Cartel, b: Cartel) -> list[str]:
    datos_a, datos_b = _datos(a), _datos(b)
    return [campo for campo in CAMPOS_COMPARADOS if datos_a[campo] != datos_b[campo]]


def _repetidas_en_el_archivo(
    candidatos: list[Candidato],
) -> tuple[list[Candidato], list[FilaReporte]]:
    """Misma clave exacta en el archivo: iguales, queda la primera; distintas, ninguna."""
    por_clave: dict[tuple[str, str], list[Candidato]] = {}
    for candidato in candidatos:
        por_clave.setdefault(candidato.clave, []).append(candidato)
    quedan: list[Candidato] = []
    rechazos: list[FilaReporte] = []
    for grupo in por_clave.values():
        primero = grupo[0]
        if all(not _distintos(primero.cartel, otro.cartel) for otro in grupo[1:]):
            quedan.append(primero)
            motivo = f"Fila repetida, igual a la fila {primero.fila}."
            rechazos += [
                FilaReporte(c.fila, c.ref_origen, RECHAZADA, motivo=motivo) for c in grupo[1:]
            ]
            continue
        motivo = "Conflicto entre las filas " + _enumerar([str(c.fila) for c in grupo]) + "."
        rechazos += [FilaReporte(c.fila, c.ref_origen, RECHAZADA, motivo=motivo) for c in grupo]
    quedan.sort(key=lambda c: c.fila)
    return quedan, rechazos


def _enumerar(partes: list[str]) -> str:
    return ", ".join(partes[:-1]) + " y " + partes[-1] if len(partes) > 1 else partes[0]


def _exacta(candidato: Candidato, existente: Cartel) -> FilaReporte:
    nombre = existente.nombre_visible
    if existente.estado.es_baja:
        motivo, resultado = "Existe dado de baja.", RECHAZADA
    elif campos := _distintos(candidato.cartel, existente):
        motivo, resultado = f"Ya existe con datos distintos: {', '.join(campos)}.", RECHAZADA
    else:
        motivo, resultado = "Ya existe.", OMITIDA
    return FilaReporte(candidato.fila, candidato.ref_origen, resultado, "", motivo, nombre)


def _parecido(candidato: Candidato, otro: Cartel) -> str | None:
    """El motivo si `otro` puede ser el mismo cartel escrito distinto; None si no se parecen."""
    aproximada = clave_aproximada(otro.direccion)
    medida, medida_otro = _medida_texto(candidato.cartel), _medida_texto(otro)
    if aproximada == candidato.aproximada and medida != medida_otro:
        if candidato.cartel.tamano and medida == "x".join(reversed(medida_otro.split("x"))):
            return f"Tamaño invertido: {otro.nombre_visible}."
        que = "otro tamaño" if candidato.cartel.tamano else "otros slots"
        return f"Misma dirección con {que}: {otro.nombre_visible}."
    if medida == medida_otro and (
        distancia_edicion(aproximada, candidato.aproximada, DISTANCIA_MAXIMA) <= DISTANCIA_MAXIMA
    ):
        return f"Posible duplicado de {otro.nombre_visible}."
    return None


# --- Carga ---


def _guardar(candidato: Candidato, nombre_archivo: str, usuario: AbstractBaseUser) -> bool:
    cartel = candidato.cartel
    try:
        with transaction.atomic():
            cartel.save()
            nuevos = {campo: _texto(getattr(cartel, campo)) for campo in CAMPOS_AUDITADOS}
            origen = f" ({candidato.ref_origen})" if candidato.ref_origen else ""
            nuevos["importacion"] = f"{nombre_archivo}{origen}"
            auditoria_services.registrar_cambios(
                "cartel",
                cartel.pk,
                dict.fromkeys(nuevos, ""),
                nuevos,
                usuario,
                origen=RegistroAuditoria.Origen.IMPORTACION,
            )
    except DatabaseError:
        return False
    return True


def _texto(valor: object) -> str:
    return "" if valor is None else str(valor)


def _motivo_creada(candidato: Candidato) -> str:
    partes = []
    if candidato.confirmado_distinto_de:
        partes.append(f"Confirmado a mano como distinto de {candidato.confirmado_distinto_de}.")
    if candidato.incompletos:
        partes.append(f"Incompleto: faltan {', '.join(candidato.incompletos)}.")
    return " ".join(partes)


def _resolver(
    candidato: Candidato,
    existentes: dict[tuple[str, str], Cartel],
    comparables: list[Cartel],
) -> FilaReporte | None:
    """El resultado si la fila no se crea, o None si se crea (con el motivo en el candidato)."""
    if existente := existentes.get(candidato.clave):
        return _exacta(candidato, existente)
    for otro in comparables:
        if motivo := _parecido(candidato, otro):
            if not candidato.confirmar_distinto:
                return FilaReporte(
                    candidato.fila,
                    candidato.ref_origen,
                    EN_REVISION,
                    "",
                    motivo,
                    otro.nombre_visible,
                )
            candidato.confirmado_distinto_de = otro.nombre_visible
            break
    return None


def importar_carteles(
    archivo: UploadedFile[bytes], formato: Formato, usuario: AbstractBaseUser, *, simular: bool
) -> Resultado:
    """Importa el CSV de un formato y devuelve el reporte (HU-015)."""
    if formato.modalidad != Formato.Modalidad.FIJA:
        raise ValidationError({"formato": "Solo se importan formatos de modalidad fija."})
    datos = _leer_filas(archivo, formato)
    catalogos = Catalogos()
    resultado = Resultado(simulado=simular)
    candidatos: list[Candidato] = []
    for numero, fila in enumerate(datos, start=2):
        validada = _validar_fila(numero, fila, formato, catalogos)
        if isinstance(validada, Candidato):
            candidatos.append(validada)
        else:
            resultado.filas += validada
    candidatos, repetidas = _repetidas_en_el_archivo(candidatos)
    resultado.filas += repetidas
    _cargar(candidatos, formato, archivo.name or "", usuario, resultado)
    resultado.filas.sort(key=lambda f: f.fila)
    return resultado


def _cargar(
    candidatos: list[Candidato],
    formato: Formato,
    nombre_archivo: str,
    usuario: AbstractBaseUser,
    resultado: Resultado,
) -> None:
    del_sistema = list(Cartel.objects.filter(formato=formato).select_related("formato", "estado"))
    existentes = {(clave_direccion(c.direccion), _medida_texto(c)): c for c in del_sistema}
    comparables = list(del_sistema)
    for candidato in candidatos:
        if fila := _resolver(candidato, existentes, comparables):
            resultado.filas.append(fila)
            continue
        guardado = resultado.simulado or _guardar(candidato, nombre_archivo, usuario)
        if not guardado:
            motivo = "No se pudo guardar el cartel."
            resultado.filas.append(
                FilaReporte(candidato.fila, candidato.ref_origen, RECHAZADA, motivo=motivo)
            )
            continue
        motivo = _motivo_creada(candidato)
        resultado.filas.append(
            FilaReporte(candidato.fila, candidato.ref_origen, CREADA, motivo=motivo)
        )
        comparables.append(candidato.cartel)
