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
from apps.inventario.models import Cartel, Formato, nombre_visible
from config.texto import normalizar_busqueda

from .models import MESES_ABREV, ParametrosDisponibilidad, Reserva

# Estados que ocupan cupo de forma dura y por eso cuentan en la validación (HU-031). Desde el
# 2026-11-17 no hay Pendientes: toda reserva nace Confirmada y su estado lo lleva el sistema
# (HU-035); RN-002 quedó sin efecto.
ESTADOS_QUE_BLOQUEAN = {Reserva.Estado.CONFIRMADA.value, Reserva.Estado.FINALIZADA.value}


def validar_campania_admite_reservas(campania: Campania) -> None:
    """Una campaña Cancelada no admite reservas nuevas (HU-024)."""
    if campania.estado == Campania.Estado.CANCELADA:
        raise ValidationError({"campania": "La campaña está cancelada: no admite reservas."})


def estado_visible(reserva: Reserva) -> str:
    """El estado que se muestra: una Confirmada que ya terminó es Finalizada (HU-036).

    Se calcula por fecha, sin tarea programada: el estado guardado no cambia.
    """
    if reserva.estado == Reserva.Estado.CONFIRMADA and reserva.fecha_fin < hoy():
        return Reserva.Estado.FINALIZADA.value
    return reserva.estado


def hoy() -> date:
    """La fecha de hoy; los tests la fijan para no depender del día en que corren."""
    return timezone.localdate()


def validar_fecha_no_pasada(fecha_fin: date) -> None:
    """Una reserva que termina antes de hoy no se carga a mano, salvo que se permita (RN-012)."""
    if fecha_fin < hoy() and not parametros_disponibilidad().permitir_fecha_pasada:
        raise ValidationError(
            {"fecha_fin": "La reserva termina antes de hoy: no se puede cargar con fecha pasada."}
        )


def validar_cartel_reservable(cartel: Cartel) -> None:
    """Un cartel de baja o fuera de servicio no admite reservas nuevas (RN-010, HU-039)."""
    if cartel.estado.es_baja:
        raise ValidationError({"cartel": "El cartel está de baja: no se puede reservar."})
    if not cartel.estado.operativo:
        raise ValidationError(
            {
                "cartel": f"El cartel está fuera de servicio ({cartel.estado.nombre}): no se "
                "puede reservar hasta que vuelva a un estado operativo."
            }
        )


def filtrar_vigentes(reservas: QuerySet[Reserva], dia: date | None = None) -> QuerySet[Reserva]:
    """Reservas activas: Confirmadas que no terminaron (HU-039)."""
    dia = dia or timezone.localdate()
    return reservas.filter(estado=Reserva.Estado.CONFIRMADA, fecha_fin__gte=dia).order_by(
        "fecha_inicio", "id"
    )


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
    return nombre_visible(
        fila["direccion"],
        fila["tamano"],
        fila["capacidad"],
        fila["formato__nombre"],
        fila["formato__por_cantidad"],
    )


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
    "formato__por_cantidad",
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
        Reserva.objects.filter(cartel=reserva.cartel, estado__in=ESTADOS_QUE_BLOQUEAN)
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
    ).select_related("campania__marca")
    por_cartel: dict[int, list[Reserva]] = {}
    for reserva in reservas:
        por_cartel.setdefault(reserva.cartel_id, []).append(reserva)
    return por_cartel


def _es_de(reserva: Reserva, campania: Campania | None) -> bool:
    """Si la reserva es de la campaña; sin campaña (alta sin guardar) ninguna lo es."""
    return campania is not None and reserva.campania_id == campania.pk


def _fila_tanda(
    cartel: Cartel,
    solapadas: list[Reserva],
    campania: Campania | None,
    rango: tuple[date, date],
    parametros: ParametrosDisponibilidad,
) -> dict[str, Any] | None:
    """Fila de "Agregar carteles", o None si el cartel no tiene cupo libre en el rango."""
    ocupados = _pico_en_rango(solapadas, *rango, parametros.borde_inclusivo)
    if ocupados >= cartel.capacidad:
        return None
    return {
        "id": cartel.pk,
        "nombre_visible": cartel.nombre_visible,
        "zona_nombre": cartel.zona.nombre,
        "proveedor_nombre": cartel.proveedor.nombre if cartel.proveedor else None,
        "tarifa_lista": str(cartel.tarifa_lista) if cartel.tarifa_lista is not None else None,
        "capacidad": cartel.capacidad,
        "ocupados": ocupados,
        "en_campania": any(_es_de(r, campania) for r in solapadas),
    }


def _carteles_filtrados(formato: Formato, filtros: dict[str, Any]) -> QuerySet[Cartel]:
    """Carteles operativos del formato que cumplen los filtros de "Agregar carteles"."""
    carteles = Cartel.objects.filter(formato=formato, estado__operativo=True, estado__es_baja=False)
    for campo in ("zona", "proveedor"):
        if filtros.get(campo) is not None:
            carteles = carteles.filter(**{f"{campo}_id": filtros[campo]})
    if filtros.get("direccion"):
        buscado = normalizar_busqueda(str(filtros["direccion"]).strip())
        carteles = carteles.filter(direccion_busqueda__icontains=buscado)
    return carteles


def _solapadas_en_rango(
    reservas: list[Reserva], desde: date, fin: date, borde_inclusivo: bool
) -> list[Reserva]:
    """Reservas que ocupan algún día de [desde, fin] según el día de borde (RN-001)."""
    return [
        r
        for r in reservas
        if r.fecha_inicio <= fin and desde <= _fin_efectivo(r.fecha_fin, borde_inclusivo)
    ]


def carteles_para_tanda(
    campania: Campania | None,
    formato: Formato,
    desde: date,
    hasta: date,
    filtros: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Carteles del formato con cupo libre en el rango, para "Agregar carteles" (HU-056).

    "Libre" es lo mismo que exige la validación dura (HU-031): pico diario (RN-003) y día de borde
    (RN-001). `en_campania` marca los que la campaña ya reservó.
    `filtros` admite `zona`, `proveedor` (IDs) y `direccion` (parcial, sin tildes).
    """
    parametros = parametros_disponibilidad()
    fin = _fin_efectivo(hasta, parametros.borde_inclusivo)
    carteles = _carteles_filtrados(formato, filtros or {})
    por_cartel = _reservas_por_cartel(carteles, desde, hasta)
    filas = []
    for cartel in carteles.select_related("formato", "zona", "proveedor").order_by(
        "direccion", "id"
    ):
        solapadas = _solapadas_en_rango(
            por_cartel.get(cartel.pk, []), desde, fin, parametros.borde_inclusivo
        )
        fila = _fila_tanda(cartel, solapadas, campania, (desde, fin), parametros)
        if fila is not None:
            filas.append(fila)
    return filas


def repartir_en_slots(
    reservas: list[Reserva], capacidad: int, borde_inclusivo: bool
) -> list[list[Reserva]]:
    """Reparte reservas en `capacidad` casilleros con partición de intervalos (HU-071).

    Ordenadas por inicio, cada reserva va al primer casillero que ya se liberó: reservas que se
    suceden comparten casillero y se usan exactamente tantos como el pico diario (RN-003). Si hay
    más solapadas que casilleros (sobreventa anterior a la validación), el resto va al último
    casillero para no esconder ninguna.
    """
    slots: list[list[Reserva]] = [[] for _ in range(capacidad)]
    for reserva in sorted(reservas, key=lambda r: (r.fecha_inicio, r.pk)):
        destino = next(
            (
                slot
                for slot in slots
                if not slot
                or _fin_efectivo(slot[-1].fecha_fin, borde_inclusivo) < reserva.fecha_inicio
            ),
            slots[-1],
        )
        destino.append(reserva)
    return slots


def _ocupante(reserva: Reserva, campania: Campania | None) -> dict[str, Any]:
    """Datos de una reserva para un casillero de la vista Posiciones."""
    marca = reserva.campania.marca
    return {
        "reserva_id": reserva.pk,
        "marca_id": marca.pk if marca else None,
        "marca_nombre": marca.nombre if marca else None,
        "campania_id": reserva.campania_id,
        "campania_nombre": reserva.campania.nombre,
        "es_esta_campania": _es_de(reserva, campania),
        "estado": reserva.estado,
        "fecha_inicio": reserva.fecha_inicio.isoformat(),
        "fecha_fin": reserva.fecha_fin.isoformat(),
    }


def _fila_posiciones(
    cartel: Cartel,
    solapadas: list[Reserva],
    campania: Campania | None,
    rango: tuple[date, date],
    parametros: ParametrosDisponibilidad,
) -> dict[str, Any]:
    """Fila de la vista Posiciones: la de la tabla más los casilleros."""
    ocupados = _pico_en_rango(solapadas, *rango, parametros.borde_inclusivo)
    slots = repartir_en_slots(solapadas, cartel.capacidad, parametros.borde_inclusivo)
    return {
        "id": cartel.pk,
        "nombre_visible": cartel.nombre_visible,
        "direccion": cartel.direccion,
        "zona_nombre": cartel.zona.nombre,
        "proveedor_nombre": cartel.proveedor.nombre if cartel.proveedor else None,
        "tarifa_lista": str(cartel.tarifa_lista) if cartel.tarifa_lista is not None else None,
        "capacidad": cartel.capacidad,
        "ocupados": ocupados,
        "lleno": ocupados >= cartel.capacidad,
        "en_campania": any(_es_de(r, campania) for r in solapadas),
        "slots": [[_ocupante(r, campania) for r in slot] for slot in slots],
    }


def posiciones_de_formato(
    campania: Campania | None,
    formato: Formato,
    desde: date,
    hasta: date,
    filtros: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Carteles del formato, llenos incluidos, con sus casilleros por slot (HU-071).

    Mismo criterio de ocupado y mismos filtros que `carteles_para_tanda`; ordenados por zona y
    dirección, como la planilla de posiciones.
    """
    parametros = parametros_disponibilidad()
    fin = _fin_efectivo(hasta, parametros.borde_inclusivo)
    carteles = _carteles_filtrados(formato, filtros or {})
    por_cartel = _reservas_por_cartel(carteles, desde, hasta)
    filas = []
    for cartel in carteles.select_related("formato", "zona", "proveedor").order_by(
        "zona__nombre", "direccion", "id"
    ):
        solapadas = _solapadas_en_rango(
            por_cartel.get(cartel.pk, []), desde, fin, parametros.borde_inclusivo
        )
        filas.append(_fila_posiciones(cartel, solapadas, campania, (desde, fin), parametros))
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
        try:
            validar_cartel_reservable(cartel)
        except ValidationError as error:
            return "fallidas", {"cartel": cartel_id, "motivo": error.message_dict["cartel"][0]}
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
        # Nace Confirmada: se valida el cupo con el cartel ya bloqueado (HU-031, HU-034).
        try:
            validar_disponibilidad(reserva)
        except ValidationError as error:
            return "fallidas", {
                "cartel": cartel_id,
                "motivo": error.message_dict["disponibilidad"][0],
            }
        reserva.save()
    return "creadas", {"cartel": cartel_id, "reserva": reserva.pk}


def crear_reservas_en_bloque(
    campania: Campania, carteles: list[int], desde: date, hasta: date
) -> dict[str, list[dict[str, Any]]]:
    """Una reserva Confirmada por cartel (HU-057), con la tarifa de lista y el nombre autogenerado.

    Es idempotente: una reserva no Cancelada de la misma campaña, cartel y fechas se informa como
    existente y no se duplica. Cada cartel va en su propia transacción y valida su cupo con el
    cartel bloqueado: el que no entra va a `fallidas` con el motivo y no frena al resto.
    """
    validar_campania_admite_reservas(campania)
    resultado: dict[str, list[dict[str, Any]]] = {"creadas": [], "existentes": [], "fallidas": []}
    for cartel_id in dict.fromkeys(carteles):
        grupo, item = _crear_en_tanda(campania, cartel_id, desde, hasta)
        resultado[grupo].append(item)
    return resultado


def _quitar(reserva: Reserva, dia: date, usuario: AbstractBaseUser | AnonymousUser) -> str:
    """Saca la reserva de su campaña (RN-006) y devuelve qué le pasó.

    Si todavía no empezó, se cancela. Si está en exhibición, termina `dia` y conserva los días
    exhibidos. Acortar solo libera días, así que no revalida cupo. Queda en auditoría.
    """
    anteriores = {"estado": reserva.estado, "fecha_fin": reserva.fecha_fin.isoformat()}
    if reserva.fecha_inicio > dia:
        reserva.estado = Reserva.Estado.CANCELADA
        resultado = "canceladas"
    else:
        reserva.fecha_fin = dia
        resultado = "terminadas"
    reserva.save()
    nuevos = {"estado": reserva.estado, "fecha_fin": reserva.fecha_fin.isoformat()}
    auditoria_services.registrar_cambios("reserva", reserva.pk, anteriores, nuevos, usuario)
    return resultado


def quitar_reserva(reserva_pk: int, usuario: AbstractBaseUser | AnonymousUser) -> Reserva:
    """La acción "Quitar" de una reserva suelta (HU-037): la cancela o la termina hoy."""
    dia = hoy()
    with transaction.atomic():
        reserva = (
            Reserva.objects.select_for_update(of=("self",))
            .select_related("cartel__formato", "campania__marca")
            .get(pk=reserva_pk)
        )
        if reserva.estado == Reserva.Estado.CANCELADA:
            raise ValidationError({"reserva": "La reserva ya está cancelada."})
        if estado_visible(reserva) == Reserva.Estado.FINALIZADA:
            raise ValidationError({"reserva": "La reserva ya terminó: no se puede quitar."})
        _quitar(reserva, dia, usuario)
    return reserva


def cancelar_campania(
    campania_pk: int, usuario: AbstractBaseUser | AnonymousUser
) -> dict[str, Any]:
    """Cancela la campaña y sus reservas en una sola transacción (HU-024, RN-006).

    Las reservas que todavía no empezaron se cancelan, las que están en exhibición terminan hoy y
    las que ya terminaron no cambian. Una campaña Cancelada no vuelve a Confirmada.
    """
    dia = hoy()
    resultado: dict[str, Any] = {"canceladas": [], "terminadas": []}
    with transaction.atomic():
        campania = Campania.objects.select_for_update().get(pk=campania_pk)
        if campania.estado == Campania.Estado.CANCELADA:
            raise ValidationError({"campania": "La campaña ya está cancelada."})
        vigentes = Reserva.objects.select_for_update(of=("self",)).select_related(
            "cartel__formato", "campania__marca"
        )
        for reserva in vigentes.filter(
            campania=campania, estado=Reserva.Estado.CONFIRMADA, fecha_fin__gte=dia
        ).order_by("id"):
            resultado[_quitar(reserva, dia, usuario)].append(reserva.pk)
        campania.estado = Campania.Estado.CANCELADA
        campania.save(update_fields=["estado", "actualizado_en"])
        auditoria_services.registrar_cambios(
            "campania",
            campania.pk,
            {"estado": Campania.Estado.CONFIRMADA.value},
            {"estado": Campania.Estado.CANCELADA.value},
            usuario,
        )
    return {"campania": campania.pk, "estado": campania.estado, **resultado}
