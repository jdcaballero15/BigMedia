"""Reglas de negocio de reservas."""

from datetime import date, timedelta
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Count, F, Q, QuerySet
from django.utils import timezone

from apps.inventario.models import Cartel

from .models import MESES_ABREV, Reserva

# Transiciones de estado válidas del ciclo de vida de la reserva (HU-035).
# La revalidación de cupo al confirmar/reactivar es de la unidad del motor (HU-031).
TRANSICIONES: dict[str, set[str]] = {
    Reserva.Estado.PENDIENTE: {Reserva.Estado.CONFIRMADA, Reserva.Estado.CANCELADA},
    Reserva.Estado.CONFIRMADA: {Reserva.Estado.FINALIZADA, Reserva.Estado.CANCELADA},
    Reserva.Estado.CANCELADA: {Reserva.Estado.CONFIRMADA},
    Reserva.Estado.FINALIZADA: set(),
}


def validar_transicion(actual: str, nuevo: str) -> None:
    if nuevo == actual:
        return
    if nuevo not in TRANSICIONES.get(actual, set()):
        raise ValidationError({"estado": f"No se puede pasar de {actual} a {nuevo}."})


def ocupacion_del_cartel(cartel: Cartel, dia: date | None = None) -> dict[str, int]:
    """Cupos ocupados vigentes sobre la capacidad del cartel, al momento (HU-040)."""
    dia = dia or timezone.localdate()
    ocupados = Reserva.objects.filter(
        cartel=cartel,
        estado__in=Reserva.ESTADOS_QUE_OCUPAN,
        fecha_inicio__lte=dia,
        fecha_fin__gte=dia,
    ).aggregate(total=Count("id"))["total"]
    return {"cartel": cartel.pk, "capacidad": cartel.capacidad, "ocupados": ocupados}


def carteles_con_ocupacion_hoy(dia: date | None = None) -> QuerySet[Cartel]:
    """Carteles no dados de baja, con `ocupados` y `cupos_libres` (hoy) anotados (HU-041).

    Ordenados por cupos libres. Se filtra y se consume con `.values(...)` en la vista.
    """
    dia = dia or timezone.localdate()
    ocupados_hoy = Count(
        "reservas",
        filter=Q(
            reservas__estado__in=Reserva.ESTADOS_QUE_OCUPAN,
            reservas__fecha_inicio__lte=dia,
            reservas__fecha_fin__gte=dia,
        ),
    )
    return (
        Cartel.objects.filter(estado__es_baja=False)
        .annotate(ocupados=ocupados_hoy)
        .annotate(cupos_libres=F("capacidad") - F("ocupados"))
        .order_by("-cupos_libres", "direccion", "id")
    )


def _nombre_visible_de_fila(fila: dict[str, Any]) -> str:
    """Replica `Cartel.nombre_visible` a partir de los campos de un `.values()`."""
    if fila["formato__nombre"] == "Séxtuples":
        return f"{fila['direccion']} · {fila['capacidad']} slots"
    if fila["tamano"]:
        return f"{fila['direccion']} · {fila['tamano']}"
    return str(fila["direccion"])


def fila_disponibilidad(fila: dict[str, Any]) -> dict[str, Any]:
    """Arma la fila de salida de la vista de disponibilidad (HU-041)."""
    return {
        "id": fila["id"],
        "nombre_visible": _nombre_visible_de_fila(fila),
        "formato_nombre": fila["formato__nombre"],
        "zona_nombre": fila["zona__nombre"],
        "modalidad": fila["formato__modalidad"],
        "capacidad": fila["capacidad"],
        "ocupados": fila["ocupados"],
        "libre": fila["ocupados"] < fila["capacidad"],
    }


CAMPOS_DISPONIBILIDAD = (
    "id",
    "direccion",
    "tamano",
    "capacidad",
    "ocupados",
    "formato__nombre",
    "formato__modalidad",
    "zona__nombre",
)

MESES_CALENDARIO_MAX = 12


def sumar_meses(fecha: date, meses: int) -> date:
    """Suma `meses` a una fecha, ajustando el día al último del mes si hace falta."""
    total = fecha.month - 1 + meses
    anio = fecha.year + total // 12
    mes = total % 12 + 1
    ultimo_dia = (date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)).toordinal() - 1
    return date.fromordinal(min(date(anio, mes, 1).toordinal() + fecha.day - 1, ultimo_dia))


def _meses_del_rango(desde: date, hasta: date) -> list[dict[str, Any]]:
    """Lista de meses [{clave: 'YYYY-MM', etiqueta: 'Oct 2026', inicio, fin}] que toca el rango."""
    meses: list[dict[str, Any]] = []
    anio, mes = desde.year, desde.month
    while (anio, mes) <= (hasta.year, hasta.month):
        primero = date(anio, mes, 1)
        ultimo = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
        ultimo = date.fromordinal(ultimo.toordinal() - 1)
        meses.append(
            {
                "clave": f"{anio:04d}-{mes:02d}",
                "etiqueta": f"{MESES_ABREV[mes - 1]} {anio}",
                "inicio": max(primero, desde),
                "fin": min(ultimo, hasta),
            }
        )
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return meses


def _pico_en_rango(reservas: list[Reserva], desde: date, hasta: date) -> int:
    """Ocupación máxima (pico diario, RN-003) de un conjunto de reservas dentro de [desde, hasta]."""
    candidatos = {desde} | {r.fecha_inicio for r in reservas if desde <= r.fecha_inicio <= hasta}
    pico = 0
    for dia in candidatos:
        cubren = sum(1 for r in reservas if r.fecha_inicio <= dia <= _fin_efectivo(r.fecha_fin))
        pico = max(pico, cubren)
    return pico


def calendario_disponibilidad(
    desde: date,
    hasta: date,
    zona: int | None = None,
    formato: int | None = None,
    modalidad: str | None = None,
) -> dict[str, Any]:
    """Grilla de carteles por mes con la ocupación pico de cada mes (HU-042)."""
    meses = _meses_del_rango(desde, hasta)
    carteles = Cartel.objects.filter(estado__es_baja=False).select_related("formato", "zona")
    if zona is not None:
        carteles = carteles.filter(zona_id=zona)
    if formato is not None:
        carteles = carteles.filter(formato_id=formato)
    if modalidad:
        carteles = carteles.filter(formato__modalidad=modalidad)
    carteles = carteles.order_by("direccion", "id")

    reservas = Reserva.objects.filter(
        cartel__in=carteles,
        estado__in=Reserva.ESTADOS_QUE_OCUPAN,
        fecha_inicio__lte=hasta,
        fecha_fin__gte=desde,
    )
    por_cartel: dict[int, list[Reserva]] = {}
    for reserva in reservas:
        por_cartel.setdefault(reserva.cartel_id, []).append(reserva)

    filas = [
        {
            "id": cartel.pk,
            "nombre_visible": cartel.nombre_visible,
            "formato_nombre": cartel.formato.nombre,
            "zona_nombre": cartel.zona.nombre,
            "capacidad": cartel.capacidad,
            "celdas": [
                {
                    "periodo": mes["clave"],
                    "ocupados": _pico_en_rango(
                        por_cartel.get(cartel.pk, []), mes["inicio"], mes["fin"]
                    ),
                }
                for mes in meses
            ],
        }
        for cartel in carteles
    ]
    periodos = [{"clave": m["clave"], "etiqueta": m["etiqueta"]} for m in meses]
    return {"periodos": periodos, "carteles": filas}


def _estados_que_bloquean() -> set[str]:
    """Estados que ocupan cupo para el bloqueo duro (RN-002)."""
    estados: set[str] = {Reserva.Estado.CONFIRMADA.value, Reserva.Estado.FINALIZADA.value}
    if settings.DISPONIBILIDAD_TENTATIVA_BLOQUEA:
        estados.add(Reserva.Estado.PENDIENTE.value)
    return estados


def _fin_efectivo(fin: date) -> date:
    """Último día que la reserva ocupa el cartel según el día de borde (RN-001)."""
    return fin if settings.DISPONIBILIDAD_BORDE_INCLUSIVO else fin - timedelta(days=1)


def validar_disponibilidad(reserva: Reserva) -> None:
    """Bloquea si el cartel no tiene cupo libre en el rango pedido (HU-031).

    Usa pico diario (RN-003): la ocupación máxima en cualquier tramo del rango, no el conteo de
    reservas que tocan el rango. Debe correr dentro de una transacción que ya bloqueó el cartel
    (`select_for_update`), para que dos confirmaciones del mismo cartel no se pisen (HU-034).
    """
    capacidad = reserva.cartel.capacidad
    fin_nueva = _fin_efectivo(reserva.fecha_fin)
    otras = Reserva.objects.filter(
        cartel=reserva.cartel, estado__in=_estados_que_bloquean()
    ).exclude(pk=reserva.pk)
    # Solo las que se solapan con el rango pedido (intervalos inclusivos con fin efectivo).
    conflictivas = [
        otra
        for otra in otras
        if otra.fecha_inicio <= fin_nueva and reserva.fecha_inicio <= _fin_efectivo(otra.fecha_fin)
    ]
    if not conflictivas:
        return

    # La ocupación solo sube en un inicio de reserva: basta mirar esos días dentro del rango.
    dias_candidatos = {reserva.fecha_inicio} | {
        otra.fecha_inicio
        for otra in conflictivas
        if reserva.fecha_inicio <= otra.fecha_inicio <= fin_nueva
    }
    pico, dia_pico = 0, reserva.fecha_inicio
    for dia in dias_candidatos:
        cubren = sum(
            1 for otra in conflictivas if otra.fecha_inicio <= dia <= _fin_efectivo(otra.fecha_fin)
        )
        if cubren > pico:
            pico, dia_pico = cubren, dia

    # La reserva nueva suma 1: si en el día pico ya hay `capacidad` ocupados, no entra.
    if pico >= capacidad:
        culpables = [
            otra.nombre
            for otra in conflictivas
            if otra.fecha_inicio <= dia_pico <= _fin_efectivo(otra.fecha_fin)
        ]
        raise ValidationError(
            {
                "disponibilidad": (
                    f"{reserva.cartel.nombre_visible}: sin cupo libre "
                    f"({pico} de {capacidad}) entre {reserva.fecha_inicio} y {reserva.fecha_fin}. "
                    f"En conflicto: {', '.join(culpables)}."
                )
            }
        )


def panel_principal() -> dict[str, object]:
    """Resumen del panel de inicio (HU-047): ocupación de hoy, campañas activas y por vencer."""
    from apps.campanias.models import Campania

    carteles = carteles_con_ocupacion_hoy()
    # `cupos_libres` es una anotación; se filtra con kwargs dinámicos.
    libres = carteles.filter(**{"cupos_libres__gt": 0}).count()
    ocupados = carteles.filter(**{"cupos_libres__lte": 0}).count()
    activas = Campania.objects.filter(estado=Campania.Estado.CONFIRMADA).count()
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=settings.PANEL_DIAS_POR_VENCER)
    por_vencer = Reserva.objects.filter(
        estado=Reserva.Estado.CONFIRMADA, fecha_fin__gte=hoy, fecha_fin__lte=limite
    ).select_related("cartel", "campania")
    return {
        "carteles_libres": libres,
        "carteles_ocupados": ocupados,
        "campanias_activas": activas,
        "por_vencer": [
            {
                "id": r.pk,
                "nombre": r.nombre,
                "cartel_nombre": r.cartel.nombre_visible,
                "campania": r.campania_id,
                "fecha_inicio": r.fecha_inicio.isoformat(),
                "fecha_fin": r.fecha_fin.isoformat(),
            }
            for r in por_vencer.order_by("fecha_fin", "id")
        ],
    }
