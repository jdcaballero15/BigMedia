"""Reglas de negocio de reservas."""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Count, F, Q, QuerySet
from django.utils import timezone

from apps.inventario.models import Cartel, Formato

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


def _dias_solape(inicio: date, fin: date, desde: date, hasta: date) -> int:
    """Cantidad de días de `[inicio, fin]` que caen en `[desde, hasta]` (inclusive ambos)."""
    lo, hi = max(inicio, desde), min(fin, hasta)
    return (hi - lo).days + 1 if hi >= lo else 0


def _porcentaje(ocupados: int, disponibles: int) -> float:
    """Ocupación en días-cupo como porcentaje de 1 decimal (HU-048)."""
    return round(ocupados / disponibles * 100, 1) if disponibles else 0.0


def _ocupacion_celda(
    reservas: list[Reserva], capacidad: int, mes: dict[str, Any]
) -> tuple[int, int]:
    """Días-cupo (ocupados, disponibles) de un cartel en un mes del período (HU-048, RN-004)."""
    dias_mes = (mes["fin"] - mes["inicio"]).days + 1
    disponibles = capacidad * dias_mes
    ocupados = sum(
        _dias_solape(r.fecha_inicio, r.fecha_fin, mes["inicio"], mes["fin"]) for r in reservas
    )
    return min(ocupados, disponibles), disponibles


def _totales_por_modalidad(
    acumulado: dict[str, dict[str, list[int]]], meses: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Evolución y total por modalidad, sin mezclar fijos con LED (HU-048)."""
    etiquetas = dict(Formato.Modalidad.choices)
    salida: list[dict[str, Any]] = []
    for modalidad, por_mes in acumulado.items():
        total_ocupados = total_disponibles = 0
        evolucion: list[dict[str, Any]] = []
        for mes in meses:
            ocupados, disponibles = por_mes.get(mes["clave"], [0, 0])
            evolucion.append(
                {"periodo": mes["clave"], "porcentaje": _porcentaje(ocupados, disponibles)}
            )
            total_ocupados += ocupados
            total_disponibles += disponibles
        salida.append(
            {
                "modalidad": modalidad,
                "etiqueta": etiquetas.get(modalidad, modalidad),
                "ocupacion": _porcentaje(total_ocupados, total_disponibles),
                "por_mes": evolucion,
            }
        )
    salida.sort(key=lambda m: m["modalidad"])
    return salida


def reporte_ocupacion(
    desde: date,
    hasta: date,
    zona: int | None = None,
    modalidad: str | None = None,
) -> dict[str, Any]:
    """Ocupación en días-cupo por cartel y mes: mapa de calor, ranking y evolución (HU-048).

    Para cada cartel no dado de baja, o de baja con reservas en el período (HU-006), y cada mes
    del período calcula los días-cupo ocupados sobre los
    disponibles (`capacidad x días`). Las filas se ordenan por ocupación del período (ranking) y los
    totales por modalidad no mezclan fijos con digitales.
    """
    meses = _meses_del_rango(desde, hasta)
    en_periodo = Reserva.objects.filter(
        estado__in=Reserva.ESTADOS_QUE_OCUPAN,
        fecha_inicio__lte=hasta,
        fecha_fin__gte=desde,
    )
    carteles = Cartel.objects.filter(
        Q(estado__es_baja=False) | Q(pk__in=en_periodo.values("cartel_id"))
    ).select_related("formato", "zona", "estado")
    if zona is not None:
        carteles = carteles.filter(zona_id=zona)
    if modalidad:
        carteles = carteles.filter(formato__modalidad=modalidad)
    carteles = carteles.order_by("direccion", "id")

    reservas = en_periodo.filter(cartel__in=carteles)
    por_cartel: dict[int, list[Reserva]] = {}
    for reserva in reservas:
        por_cartel.setdefault(reserva.cartel_id, []).append(reserva)

    filas: list[dict[str, Any]] = []
    acumulado: dict[str, dict[str, list[int]]] = {}
    for cartel in carteles:
        propias = por_cartel.get(cartel.pk, [])
        celdas: list[dict[str, Any]] = []
        total_ocupados = total_disponibles = 0
        for mes in meses:
            ocupados, disponibles = _ocupacion_celda(propias, cartel.capacidad, mes)
            celdas.append(
                {
                    "periodo": mes["clave"],
                    "porcentaje": _porcentaje(ocupados, disponibles),
                    "dias_ocupados": ocupados,
                    "dias_disponibles": disponibles,
                }
            )
            total_ocupados += ocupados
            total_disponibles += disponibles
            slot = acumulado.setdefault(cartel.formato.modalidad, {}).setdefault(
                mes["clave"], [0, 0]
            )
            slot[0] += ocupados
            slot[1] += disponibles
        filas.append(
            {
                "id": cartel.pk,
                "nombre_visible": cartel.nombre_visible,
                "modalidad": cartel.formato.modalidad,
                "zona_nombre": cartel.zona.nombre,
                "formato_nombre": cartel.formato.nombre,
                "de_baja": cartel.estado.es_baja,
                "ocupacion": _porcentaje(total_ocupados, total_disponibles),
                "celdas": celdas,
            }
        )
    filas.sort(key=lambda f: f["ocupacion"], reverse=True)
    periodos = [{"clave": m["clave"], "etiqueta": m["etiqueta"]} for m in meses]
    return {
        "periodos": periodos,
        "carteles": filas,
        "modalidades": _totales_por_modalidad(acumulado, meses),
    }


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


def reparto_por_mes(reserva: Reserva) -> list[dict[str, Any]]:
    """Reparte `reserva.total` entre los meses del rango, proporcional a los días (HU-051).

    Días por mes = días de `[fecha_inicio, fecha_fin]` que caen en ese mes (inclusive ambos
    extremos). El último mes absorbe el redondeo, para que la suma coincida con el total al
    centavo. Sirve igual para alquileres mensuales y de 15 días. Devuelve
    `[{mes, etiqueta, monto}]` ordenado por mes.
    """
    meses = _meses_del_rango(reserva.fecha_inicio, reserva.fecha_fin)
    dias_totales = (reserva.fecha_fin - reserva.fecha_inicio).days + 1
    total = reserva.total
    acumulado = Decimal("0.00")
    reparto: list[dict[str, Any]] = []
    for indice, mes in enumerate(meses):
        if indice == len(meses) - 1:
            monto = total - acumulado
        else:
            dias_mes = (mes["fin"] - mes["inicio"]).days + 1
            monto = (total * dias_mes / dias_totales).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            acumulado += monto
        reparto.append({"mes": mes["clave"], "etiqueta": mes["etiqueta"], "monto": monto})
    return reparto


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
