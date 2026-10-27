"""Reglas de negocio de reservas."""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, F, Q, QuerySet
from django.utils import timezone

from apps.auditoria import services as auditoria_services
from apps.campanias.models import Campania
from apps.inventario.models import Cartel, Formato
from config.texto import normalizar_busqueda

from .models import MESES_ABREV, ParametrosDisponibilidad, Reserva

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


# Una reserva nace Pendiente o Confirmada (HU-035); las históricas Finalizadas entran por HU-038.
ESTADOS_INICIALES = {Reserva.Estado.PENDIENTE, Reserva.Estado.CONFIRMADA}

# Estados que ocupan cupo de forma dura y por eso pasan por la validación (HU-031).
ESTADOS_CON_VALIDACION_DURA = {Reserva.Estado.CONFIRMADA, Reserva.Estado.FINALIZADA}


def validar_estado_inicial(estado: str) -> None:
    if estado not in ESTADOS_INICIALES:
        raise ValidationError(
            {"estado": "Una reserva nueva solo puede crearse Pendiente o Confirmada."}
        )


def necesita_validar_cupo(anterior: str | None, nuevo: str, cambia_ocupacion: bool) -> bool:
    """Si guardar la reserva exige validar el cupo. `anterior` es None en un alta.

    Valida cuando la reserva queda ocupando de forma dura y antes no lo hacía, o cuando ya
    ocupaba y cambian sus fechas o su cartel. Confirmada -> Finalizada sin otros cambios no
    revalida: ese cupo ya estaba validado.
    """
    if nuevo not in ESTADOS_CON_VALIDACION_DURA:
        return False
    return anterior not in ESTADOS_CON_VALIDACION_DURA or cambia_ocupacion


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


def _pico_en_rango(reservas: list[Reserva], desde: date, hasta: date, borde_inclusivo: bool) -> int:
    """Ocupación máxima (pico diario, RN-003) de un conjunto de reservas dentro de [desde, hasta]."""
    candidatos = {desde} | {r.fecha_inicio for r in reservas if desde <= r.fecha_inicio <= hasta}
    pico = 0
    for dia in candidatos:
        cubren = sum(
            1
            for r in reservas
            if r.fecha_inicio <= dia <= _fin_efectivo(r.fecha_fin, borde_inclusivo)
        )
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
    borde_inclusivo = parametros_disponibilidad().borde_inclusivo
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
                        por_cartel.get(cartel.pk, []), mes["inicio"], mes["fin"], borde_inclusivo
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


def parametros_disponibilidad() -> ParametrosDisponibilidad:
    """Parámetros vigentes del motor de disponibilidad (HU-001).

    Se leen de la base en cada uso, sin caché, para que un cambio rija en la validación siguiente.
    """
    parametros, _ = ParametrosDisponibilidad.objects.get_or_create(pk=1)
    return parametros


def _estados_que_bloquean(tentativa_bloquea: bool) -> set[str]:
    """Estados que ocupan cupo para el bloqueo duro (RN-002)."""
    estados: set[str] = {Reserva.Estado.CONFIRMADA.value, Reserva.Estado.FINALIZADA.value}
    if tentativa_bloquea:
        estados.add(Reserva.Estado.PENDIENTE.value)
    return estados


def _fin_efectivo(fin: date, borde_inclusivo: bool) -> date:
    """Último día que la reserva ocupa el cartel según el día de borde (RN-001)."""
    return fin if borde_inclusivo else fin - timedelta(days=1)


def conflictos_de(reserva: Reserva) -> list[Reserva]:
    """Reservas que ocupan el cupo en el día pico si `reserva` no entra; vacía si entra (HU-031).

    Usa pico diario (RN-003): la ocupación máxima en cualquier tramo del rango, no el conteo de
    reservas que tocan el rango. Debe correr dentro de una transacción que ya bloqueó el cartel
    (`select_for_update`), para que dos confirmaciones del mismo cartel no se pisen (HU-034).
    Los parámetros se leen dentro de esa misma transacción (HU-001).
    """
    parametros = parametros_disponibilidad()
    borde = parametros.borde_inclusivo
    fin_nueva = _fin_efectivo(reserva.fecha_fin, borde)
    otras = (
        Reserva.objects.filter(
            cartel=reserva.cartel, estado__in=_estados_que_bloquean(parametros.tentativa_bloquea)
        )
        .exclude(pk=reserva.pk)
        .select_related("campania")
    )
    # Solo las que se solapan con el rango pedido (intervalos inclusivos con fin efectivo).
    solapadas = [
        otra
        for otra in otras
        if otra.fecha_inicio <= fin_nueva
        and reserva.fecha_inicio <= _fin_efectivo(otra.fecha_fin, borde)
    ]
    # La ocupación solo sube en un inicio de reserva: basta mirar esos días dentro del rango.
    dias_candidatos = {reserva.fecha_inicio} | {
        otra.fecha_inicio
        for otra in solapadas
        if reserva.fecha_inicio <= otra.fecha_inicio <= fin_nueva
    }
    culpables: list[Reserva] = []
    for dia in sorted(dias_candidatos):
        cubren = [
            o for o in solapadas if o.fecha_inicio <= dia <= _fin_efectivo(o.fecha_fin, borde)
        ]
        if len(cubren) > len(culpables):
            culpables = cubren
    # La reserva nueva suma 1: si en el día pico ya hay `capacidad` ocupados, no entra.
    return culpables if len(culpables) >= reserva.cartel.capacidad else []


def validar_disponibilidad(reserva: Reserva) -> None:
    """Bloquea si el cartel no tiene cupo libre en el rango pedido (HU-031); ver `conflictos_de`."""
    culpables = conflictos_de(reserva)
    if not culpables:
        return
    raise ValidationError(
        {
            "disponibilidad": (
                f"{reserva.cartel.nombre_visible}: sin cupo libre "
                f"({len(culpables)} de {reserva.cartel.capacidad}) "
                f"entre {reserva.fecha_inicio} y {reserva.fecha_fin}. "
                f"En conflicto: {', '.join(otra.nombre for otra in culpables)}."
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


def _fila_seguimiento(
    linea: int | None, formato: int, nombre: str, solicitadas: int | None, reservadas: int
) -> dict[str, Any]:
    if solicitadas is None:
        faltantes, excedente = None, None
    else:
        faltantes = max(0, solicitadas - reservadas)
        excedente = max(0, reservadas - solicitadas)
    return {
        "linea": linea,
        "formato": formato,
        "formato_nombre": nombre,
        "solicitadas": solicitadas,
        "reservadas": reservadas,
        "faltantes": faltantes,
        "excedente": excedente,
    }


def seguimiento_de_campania(campania: Campania) -> list[dict[str, Any]]:
    """Solicitado, reservado y faltante por formato de la campaña (HU-058).

    Reservada es toda reserva no Cancelada de la campaña cuyo cartel es del formato. Los formatos
    con reservas pero sin línea activa se muestran aparte, sin cantidad solicitada.
    """
    reservadas = dict(
        Reserva.objects.filter(campania=campania)
        .exclude(estado=Reserva.Estado.CANCELADA)
        .values("cartel__formato")
        .annotate(total=Count("id"))
        .values_list("cartel__formato", "total")
    )
    filas = [
        _fila_seguimiento(
            linea.pk,
            linea.formato_id,
            linea.formato.nombre,
            linea.cantidad,
            reservadas.pop(linea.formato_id, 0),
        )
        for linea in campania.lineas.filter(activa=True).select_related("formato")
    ]
    for formato in Formato.objects.filter(pk__in=reservadas).order_by("nombre"):
        filas.append(
            _fila_seguimiento(None, formato.pk, formato.nombre, None, reservadas[formato.pk])
        )
    return filas


def _reservas_por_cartel(
    carteles: QuerySet[Cartel], desde: date, hasta: date
) -> dict[int, list[Reserva]]:
    """Reservas que ocupan y tocan el rango, de todos los carteles en una sola consulta."""
    reservas = Reserva.objects.filter(
        cartel__in=carteles,
        estado__in=Reserva.ESTADOS_QUE_OCUPAN,
        fecha_inicio__lte=hasta,
        fecha_fin__gte=desde,
    )
    por_cartel: dict[int, list[Reserva]] = {}
    for reserva in reservas:
        por_cartel.setdefault(reserva.cartel_id, []).append(reserva)
    return por_cartel


def _fila_tanda(
    cartel: Cartel,
    solapadas: list[Reserva],
    campania: Campania,
    rango: tuple[date, date],
    parametros: ParametrosDisponibilidad,
) -> dict[str, Any] | None:
    """Fila de "Agregar carteles", o None si el cartel no tiene cupo libre en el rango."""
    bloquean = _estados_que_bloquean(parametros.tentativa_bloquea)
    ocupados = _pico_en_rango(
        [r for r in solapadas if r.estado in bloquean], *rango, parametros.borde_inclusivo
    )
    if ocupados >= cartel.capacidad:
        return None
    tentativas = sum(
        1 for r in solapadas if r.estado not in bloquean and r.campania_id != campania.pk
    )
    return {
        "id": cartel.pk,
        "nombre_visible": cartel.nombre_visible,
        "zona_nombre": cartel.zona.nombre,
        "proveedor_nombre": cartel.proveedor.nombre if cartel.proveedor else None,
        "tarifa_lista": str(cartel.tarifa_lista) if cartel.tarifa_lista is not None else None,
        "capacidad": cartel.capacidad,
        "ocupados": ocupados,
        "tentativas": tentativas,
        "en_campania": any(r.campania_id == campania.pk for r in solapadas),
    }


def carteles_para_tanda(
    campania: Campania,
    formato: Formato,
    desde: date,
    hasta: date,
    filtros: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Carteles del formato con cupo libre en el rango, para "Agregar carteles" (HU-056).

    "Libre" es lo mismo que exige la validación dura (HU-031): pico diario (RN-003), día de borde
    (RN-001) y Pendientes según el parámetro (RN-002). Las Pendientes de otras campañas que no
    bloquean se informan como `tentativas`; `en_campania` marca los que la campaña ya reservó.
    `filtros` admite `zona`, `proveedor` (IDs) y `direccion` (parcial, sin tildes).
    """
    filtros = filtros or {}
    parametros = parametros_disponibilidad()
    fin = _fin_efectivo(hasta, parametros.borde_inclusivo)
    carteles = Cartel.objects.filter(formato=formato, estado__es_baja=False)
    for campo in ("zona", "proveedor"):
        if filtros.get(campo) is not None:
            carteles = carteles.filter(**{f"{campo}_id": filtros[campo]})
    if filtros.get("direccion"):
        buscado = normalizar_busqueda(str(filtros["direccion"]).strip())
        carteles = carteles.filter(direccion_busqueda__icontains=buscado)
    por_cartel = _reservas_por_cartel(carteles, desde, hasta)
    filas = []
    for cartel in carteles.select_related("formato", "zona", "proveedor").order_by(
        "direccion", "id"
    ):
        solapadas = [
            r
            for r in por_cartel.get(cartel.pk, [])
            if r.fecha_inicio <= fin
            and desde <= _fin_efectivo(r.fecha_fin, parametros.borde_inclusivo)
        ]
        fila = _fila_tanda(cartel, solapadas, campania, (desde, fin), parametros)
        if fila is not None:
            filas.append(fila)
    return filas


def _crear_en_tanda(
    campania: Campania, cartel_id: int, desde: date, hasta: date
) -> tuple[str, dict[str, Any]]:
    """Crea la reserva de un cartel de la tanda; devuelve en qué grupo del resumen va."""
    with transaction.atomic():
        # Bloquea solo el cartel, como el alta individual (HU-034).
        cartel = (
            Cartel.objects.select_for_update(of=("self",))
            .select_related("estado", "formato")
            .filter(pk=cartel_id)
            .first()
        )
        if cartel is None:
            return "fallidas", {"cartel": cartel_id, "motivo": "No existe el cartel."}
        if cartel.estado.es_baja:
            motivo = "El cartel está de baja: no se puede reservar."
            return "fallidas", {"cartel": cartel_id, "motivo": motivo}
        existente = (
            Reserva.objects.filter(
                campania=campania, cartel=cartel, fecha_inicio=desde, fecha_fin=hasta
            )
            .exclude(estado=Reserva.Estado.CANCELADA)
            .first()
        )
        if existente is not None:
            return "existentes", {"cartel": cartel_id, "reserva": existente.pk}
        tarifa = cartel.tarifa_lista
        reserva = Reserva(
            campania=campania,
            cartel=cartel,
            fecha_inicio=desde,
            fecha_fin=hasta,
            precio_alquiler=tarifa if tarifa is not None else Decimal("0.00"),
        )
        reserva.save()
    return "creadas", {"cartel": cartel_id, "reserva": reserva.pk}


def crear_reservas_en_bloque(
    campania: Campania, carteles: list[int], desde: date, hasta: date
) -> dict[str, list[dict[str, Any]]]:
    """Una reserva Pendiente por cartel (HU-057), con la tarifa de lista y el nombre autogenerado.

    Es idempotente: una reserva no Cancelada de la misma campaña, cartel y fechas se informa como
    existente y no se duplica. Cada cartel va en su propia transacción, así una falla no frena al
    resto. Como en el alta individual, crear una Pendiente no valida cupo: eso pasa al confirmar.
    """
    resultado: dict[str, list[dict[str, Any]]] = {"creadas": [], "existentes": [], "fallidas": []}
    for cartel_id in dict.fromkeys(carteles):
        grupo, item = _crear_en_tanda(campania, cartel_id, desde, hasta)
        resultado[grupo].append(item)
    return resultado


def _conflicto(reserva: Reserva, culpables: list[Reserva]) -> dict[str, Any]:
    campanias = {otra.campania_id: str(otra.campania) for otra in culpables}
    return {
        "reserva": reserva.pk,
        "nombre": reserva.nombre,
        "cartel_nombre": reserva.cartel.nombre_visible,
        "fecha_inicio": reserva.fecha_inicio.isoformat(),
        "fecha_fin": reserva.fecha_fin.isoformat(),
        "ocupada_por": [
            {"campania": pk, "campania_nombre": nombre} for pk, nombre in campanias.items()
        ],
    }


def _confirmar_pendiente(
    reserva_pk: int, usuario: AbstractBaseUser | AnonymousUser
) -> tuple[bool, dict[str, Any] | None]:
    """Confirma una Pendiente con el cartel bloqueado (HU-034).

    Devuelve si se confirmó y, si no entra, su conflicto. Si mientras tanto dejó de estar
    Pendiente, no se confirmó ni tiene conflicto.
    """
    with transaction.atomic():
        cartel_pk = Reserva.objects.values_list("cartel_id", flat=True).get(pk=reserva_pk)
        Cartel.objects.select_for_update().get(pk=cartel_pk)
        # Se relee con el cartel bloqueado: otro pedido pudo haberla confirmado o cancelado.
        reserva = Reserva.objects.select_related("cartel__formato", "campania__marca").get(
            pk=reserva_pk
        )
        if reserva.estado != Reserva.Estado.PENDIENTE:
            return False, None
        culpables = conflictos_de(reserva)
        if culpables:
            return False, _conflicto(reserva, culpables)
        reserva.estado = Reserva.Estado.CONFIRMADA
        reserva.save()
        auditoria_services.registrar_cambios(
            "reserva",
            reserva.pk,
            {"estado": Reserva.Estado.PENDIENTE.value},
            {"estado": Reserva.Estado.CONFIRMADA.value},
            usuario,
        )
    return True, None


def confirmar_reservas_de_campania(
    campania: Campania, usuario: AbstractBaseUser | AnonymousUser
) -> dict[str, list[Any]]:
    """Confirma las Pendientes de la campaña que entran y lista las que no (HU-059).

    Exige la campaña Confirmada. Cada Pendiente va en su propia transacción con el cartel
    bloqueado, con la misma validación que la confirmación individual (HU-031, HU-034). Repetir
    solo procesa lo que sigue Pendiente.
    """
    if campania.estado != Campania.Estado.CONFIRMADA:
        raise ValidationError({"campania": "Primero confirmá la campaña."})
    pendientes = Reserva.objects.filter(
        campania=campania, estado=Reserva.Estado.PENDIENTE
    ).order_by("creado_en", "id")
    confirmadas: list[int] = []
    conflictos: list[dict[str, Any]] = []
    for reserva_pk in list(pendientes.values_list("pk", flat=True)):
        confirmada, conflicto = _confirmar_pendiente(reserva_pk, usuario)
        if confirmada:
            confirmadas.append(reserva_pk)
        if conflicto is not None:
            conflictos.append(conflicto)
    return {"confirmadas": confirmadas, "conflictos": conflictos}


def mover_pendientes(
    campania: Campania,
    inicio_anterior: date,
    fin_anterior: date,
    usuario: AbstractBaseUser | AnonymousUser,
) -> list[int]:
    """Lleva a las fechas actuales de la campaña sus Pendientes con las fechas anteriores (HU-058).

    Solo mueve las que tenían exactamente las fechas anteriores de la campaña: una tanda cargada
    con otras fechas no se pisa. Las Confirmadas no se tocan. Como toda edición de una Pendiente,
    no valida cupo (RN-002); eso pasa al confirmar.
    """
    if campania.fecha_inicio is None or campania.fecha_fin is None:
        raise ValidationError({"campania": "La campaña no tiene fechas."})
    movidas: list[int] = []
    with transaction.atomic():
        reservas = Reserva.objects.select_related("cartel__formato", "campania__marca").filter(
            campania=campania,
            estado=Reserva.Estado.PENDIENTE,
            fecha_inicio=inicio_anterior,
            fecha_fin=fin_anterior,
        )
        for reserva in reservas.order_by("id"):
            anteriores = {
                "fecha_inicio": str(reserva.fecha_inicio),
                "fecha_fin": str(reserva.fecha_fin),
            }
            reserva.fecha_inicio = campania.fecha_inicio
            reserva.fecha_fin = campania.fecha_fin
            reserva.save()
            nuevos = {
                "fecha_inicio": str(reserva.fecha_inicio),
                "fecha_fin": str(reserva.fecha_fin),
            }
            auditoria_services.registrar_cambios("reserva", reserva.pk, anteriores, nuevos, usuario)
            movidas.append(reserva.pk)
    return movidas
