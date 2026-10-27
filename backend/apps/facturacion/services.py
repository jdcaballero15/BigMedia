"""Reglas de facturación: ítems a facturar (HU-060, HU-061, HU-065) y reportes de ingresos."""

import io
from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from openpyxl import Workbook

from apps.auditoria import services as auditoria_services
from apps.reservas.models import MESES_ABREV, Reserva
from apps.reservas.services import reparto_por_mes

from .models import EnvioFacturacion, ItemFacturacion, al_centavo

CERO = Decimal("0.00")


def _dias_solape(inicio: date, fin: date, desde: date, hasta: date) -> int:
    """Días de `[inicio, fin]` que caen en `[desde, hasta]` (inclusive ambos)."""
    lo, hi = max(inicio, desde), min(fin, hasta)
    return (hi - lo).days + 1 if hi >= lo else 0


def _meses_periodo(desde: date, hasta: date) -> list[dict[str, str]]:
    """Columnas del reporte: cada mes entre `desde` y `hasta` como {mes, etiqueta}."""
    meses: list[dict[str, str]] = []
    anio, mes = desde.year, desde.month
    while (anio, mes) <= (hasta.year, hasta.month):
        meses.append({"mes": f"{anio:04d}-{mes:02d}", "etiqueta": f"{MESES_ABREV[mes - 1]} {anio}"})
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return meses


def _acumular_reserva(
    acumulador: dict[int | None, dict[str, Any]], reserva: Reserva, claves: set[str]
) -> None:
    """Suma los montos del reparto de una reserva en su cliente y su marca (HU-049)."""
    montos = {i["mes"]: i["monto"] for i in reparto_por_mes(reserva) if i["mes"] in claves}
    if not montos:
        return
    cliente = reserva.campania.cliente_factura
    marca = reserva.campania.marca
    cl = acumulador.setdefault(
        cliente.pk if cliente else None,
        {
            "cliente": cliente.pk if cliente else None,
            "nombre": cliente.nombre_visible if cliente else "Sin cliente",
            "por_mes": {},
            "marcas": {},
        },
    )
    ma = cl["marcas"].setdefault(
        marca.pk if marca else None,
        {"marca": marca.pk if marca else None, "nombre": marca.nombre if marca else "Sin marca",
         "por_mes": {}},
    )  # fmt: skip
    for mes, monto in montos.items():
        cl["por_mes"][mes] = cl["por_mes"].get(mes, CERO) + monto
        ma["por_mes"][mes] = ma["por_mes"].get(mes, CERO) + monto


def _total(por_mes: dict[str, Decimal]) -> Decimal:
    acumulado = CERO
    for monto in por_mes.values():
        acumulado += monto
    return acumulado


def _fmt(valor: Decimal) -> str:
    """Importe como string de 2 decimales (contrato de dinero, como el reporte de costos)."""
    return f"{valor:.2f}"


def _por_mes_str(por_mes: dict[str, Decimal], claves: set[str]) -> dict[str, str]:
    """Meses del período en orden, con 0.00 donde no hubo monto, como string."""
    return {mes: _fmt(por_mes.get(mes, CERO)) for mes in sorted(claves)}


def _ordenar(
    acumulador: dict[int | None, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Arma clientes y marcas con total `Decimal` y ranking (orden por total descendente)."""
    clientes: list[dict[str, Any]] = []
    for cl in acumulador.values():
        marcas = sorted(
            (
                {
                    "marca": ma["marca"],
                    "nombre": ma["nombre"],
                    "total": _total(ma["por_mes"]),
                    "por_mes": ma["por_mes"],
                }
                for ma in cl["marcas"].values()
            ),
            key=lambda m: m["total"],
            reverse=True,
        )
        clientes.append(
            {
                "cliente": cl["cliente"],
                "nombre": cl["nombre"],
                "total": _total(cl["por_mes"]),
                "por_mes": cl["por_mes"],
                "marcas": marcas,
            }
        )
    clientes.sort(key=lambda c: c["total"], reverse=True)
    return clientes


def _formatear_cliente(cl: dict[str, Any], claves: set[str]) -> dict[str, Any]:
    """Pasa un cliente ya ordenado a la salida con importes como string."""
    return {
        "cliente": cl["cliente"],
        "nombre": cl["nombre"],
        "total": _fmt(cl["total"]),
        "por_mes": _por_mes_str(cl["por_mes"], claves),
        "marcas": [
            {
                "marca": ma["marca"],
                "nombre": ma["nombre"],
                "total": _fmt(ma["total"]),
                "por_mes": _por_mes_str(ma["por_mes"], claves),
            }
            for ma in cl["marcas"]
        ],
    }


def reporte_por_rubro(desde: date, hasta: date) -> dict[str, Any]:
    """Ingresos y días-cupo por rubro de la marca, para el período dado (HU-050, criterio 1).

    Para cada reserva que ocupa cupo y se solapa con `[desde, hasta]`, acumula:
    - ingresos: suma del reparto por mes (HU-051) dentro del período.
    - días-cupo: días de solape de la reserva con el período (una reserva = un cupo, RN-004).
    Agrupa por rubro de la marca de la campaña. Marca sin rubro → "Sin rubro". Ordena por
    ingresos descendente. Los importes salen como string de 2 decimales.
    """
    claves = {p["mes"] for p in _meses_periodo(desde, hasta)}
    reservas = Reserva.objects.filter(
        estado__in=Reserva.ESTADOS_QUE_OCUPAN, fecha_inicio__lte=hasta, fecha_fin__gte=desde
    ).select_related("campania__marca__rubro")

    acumulador: dict[int | None, dict[str, Any]] = {}
    for reserva in reservas:
        marca = reserva.campania.marca
        rubro = marca.rubro if marca is not None else None
        clave_rubro = rubro.pk if rubro is not None else None
        nombre_rubro = rubro.nombre if rubro is not None else "Sin rubro"

        montos = {i["mes"]: i["monto"] for i in reparto_por_mes(reserva) if i["mes"] in claves}
        ingresos_reserva = sum(montos.values(), CERO)
        dias = _dias_solape(reserva.fecha_inicio, reserva.fecha_fin, desde, hasta)

        bucket = acumulador.setdefault(
            clave_rubro,
            {"rubro": clave_rubro, "nombre": nombre_rubro, "ingresos": CERO, "dias_cupo": 0},
        )
        bucket["ingresos"] = bucket["ingresos"] + ingresos_reserva
        bucket["dias_cupo"] = bucket["dias_cupo"] + dias

    total_ingresos = sum((b["ingresos"] for b in acumulador.values()), CERO)
    total_dias_cupo = sum(b["dias_cupo"] for b in acumulador.values())

    rubros = sorted(acumulador.values(), key=lambda b: b["ingresos"], reverse=True)
    rubros_out = [
        {
            "rubro": b["rubro"],
            "nombre": b["nombre"],
            "ingresos": _fmt(b["ingresos"]),
            "dias_cupo": b["dias_cupo"],
            "porcentaje_ocupacion": (
                round(b["dias_cupo"] / total_dias_cupo * 100, 1) if total_dias_cupo else 0.0
            ),
        }
        for b in rubros
    ]
    return {
        "rubros": rubros_out,
        "total_ingresos": _fmt(total_ingresos),
        "total_dias_cupo": total_dias_cupo,
    }


def reporte_ingresos(desde: date, hasta: date) -> dict[str, Any]:
    """Facturación del período con desglose cliente → marca, repartida por mes (HU-049).

    Toma las reservas que ocupan cupo (no canceladas) y se solapan con `[desde, hasta]`, reparte el
    ingreso de cada una por mes (HU-051) y acumula por cliente que factura (RN-014) y por marca. Los
    totales cuadran: cliente = suma de marcas = suma de meses; global = suma de clientes. Los importes
    salen como string de 2 decimales.
    """
    periodos = _meses_periodo(desde, hasta)
    claves = {p["mes"] for p in periodos}
    reservas = Reserva.objects.filter(
        estado__in=Reserva.ESTADOS_QUE_OCUPAN, fecha_inicio__lte=hasta, fecha_fin__gte=desde
    ).select_related("campania__marca__cliente", "campania__cliente_facturacion")
    acumulador: dict[int | None, dict[str, Any]] = {}
    for reserva in reservas:
        _acumular_reserva(acumulador, reserva, claves)
    ordenados = _ordenar(acumulador)
    total = CERO
    for cl in ordenados:
        total += cl["total"]
    clientes = [_formatear_cliente(cl, claves) for cl in ordenados]
    return {"periodos": periodos, "clientes": clientes, "total": _fmt(total)}


# Transiciones de estado del ítem (HU-065). Borrador pasa a Enviado solo con "Enviar a facturar"
# (HU-066); corregir un Facturado espera RN-026.
TRANSICIONES_ITEM: dict[str, set[str]] = {
    ItemFacturacion.Estado.BORRADOR: {ItemFacturacion.Estado.ANULADO},
    ItemFacturacion.Estado.ENVIADO: {
        ItemFacturacion.Estado.FACTURADO,
        ItemFacturacion.Estado.ANULADO,
    },
    ItemFacturacion.Estado.FACTURADO: set(),
    ItemFacturacion.Estado.ANULADO: set(),
}
# Fuera de Borrador solo se cambia el estado (y el número al facturar); reabrir es HU-067.
CAMPOS_FUERA_DE_BORRADOR = {"estado", "numero_factura"}


def _etiqueta(estado: str) -> str:
    return str(ItemFacturacion.Estado(estado).label)


def _validar_estado(actual: str, nuevo: str, campos: set[str]) -> None:
    if actual != ItemFacturacion.Estado.BORRADOR and campos - CAMPOS_FUERA_DE_BORRADOR:
        raise ValidationError({"estado": "Solo se pueden editar los datos de un ítem en Borrador."})
    if nuevo != actual and nuevo not in TRANSICIONES_ITEM[actual]:
        raise ValidationError(
            {"estado": f"No se puede pasar de {_etiqueta(actual)} a {_etiqueta(nuevo)}."}
        )


def _validar_numero_factura(actual: str, nuevo: str, numero: str, cargado: bool) -> None:
    if nuevo == ItemFacturacion.Estado.FACTURADO and actual != nuevo and not numero:
        raise ValidationError(
            {"numero_factura": "Cargá el número de factura para pasar el ítem a Facturado."}
        )
    if cargado and nuevo != ItemFacturacion.Estado.FACTURADO:
        raise ValidationError(
            {"numero_factura": "El número de factura se carga al pasar el ítem a Facturado."}
        )


def validar_cambio_de_item(item: ItemFacturacion | None, datos: dict[str, Any]) -> None:
    """Estados y número de factura de un alta (`item` None) o una edición (HU-065)."""
    if item is None:
        if datos.get("estado", ItemFacturacion.Estado.BORRADOR) != ItemFacturacion.Estado.BORRADOR:
            raise ValidationError({"estado": "Un ítem nuevo nace en Borrador."})
        actual = ItemFacturacion.Estado.BORRADOR.value
    else:
        actual = item.estado
    nuevo = datos.get("estado", actual)
    _validar_estado(actual, nuevo, set(datos))
    numero = datos.get("numero_factura", getattr(item, "numero_factura", "")).strip()
    _validar_numero_factura(actual, nuevo, numero, "numero_factura" in datos)


def totales_del_mes(mes: date) -> dict[str, Any]:
    """Neto, IVA y total de los ítems del mes, sin los anulados (HU-065, criterio 3)."""
    fila = (
        ItemFacturacion.objects.filter(mes=mes)
        .exclude(estado=ItemFacturacion.Estado.ANULADO)
        .aggregate(cantidad=Count("id"), neto=Sum("neto"), iva=Sum("iva"), total=Sum("total"))
    )
    return {
        "mes": mes.strftime("%Y-%m"),
        "cantidad": fila["cantidad"],
        **{campo: str(al_centavo(fila[campo] or CERO)) for campo in ("neto", "iva", "total")},
    }


def faltantes_para_enviar(item: ItemFacturacion) -> list[str]:
    """Lo que se exige al enviar a facturar (HU-066): cliente, importe neto y mes."""
    faltan = []
    if item.cliente_id is None:
        faltan.append("cliente")
    if item.neto is None:
        faltan.append("importe neto")
    if item.mes is None:
        faltan.append("mes")
    return faltan


def enviar_a_facturar(
    mes: date, usuario: AbstractBaseUser
) -> tuple[EnvioFacturacion | None, list[dict[str, Any]]]:
    """Pasa a Enviado los Borradores completos del mes y registra el envío (HU-066).

    Los incompletos no se envían y se devuelven con lo que les falta (RN-025). Bloquea los
    Borradores del mes, así dos envíos simultáneos no mandan un ítem dos veces. Sin ítems
    completos no crea un envío.
    """
    with transaction.atomic():
        borradores = list(
            ItemFacturacion.objects.select_for_update()
            .filter(mes=mes, estado=ItemFacturacion.Estado.BORRADOR)
            .order_by("id")
        )
        completos = [item for item in borradores if not faltantes_para_enviar(item)]
        incompletos = [
            {
                "item": item.pk,
                "descripcion": item.descripcion or "Sin descripción",
                "faltan": faltantes_para_enviar(item),
            }
            for item in borradores
            if faltantes_para_enviar(item)
        ]
        if not completos:
            return None, incompletos
        envio = EnvioFacturacion.objects.create(mes=mes, enviado_por_id=usuario.pk)
        envio.items.set(completos)
        for item in completos:
            item.estado = ItemFacturacion.Estado.ENVIADO
            item.save(update_fields=["estado", "actualizado_en"])
            auditoria_services.registrar_cambios(
                "item_facturacion",
                item.pk,
                {"estado": ItemFacturacion.Estado.BORRADOR.value},
                {"estado": ItemFacturacion.Estado.ENVIADO.value},
                usuario,
            )
    return envio, incompletos


def _numero(valor: Decimal | None) -> float | None:
    return float(valor) if valor is not None else None


# Columnas de la planilla para Administración (RN-024, provisoria hasta tener la planilla real):
# las de hoy y, al final, las nuevas. Orden de compra (HU-062) y grupo (HU-064) llegan el 04/11.
COLUMNAS_PLANILLA: list[tuple[str, Any]] = [
    ("Mes", lambda i: i.mes.strftime("%Y-%m") if i.mes else None),
    ("Cliente", lambda i: i.cliente.nombre_visible if i.cliente else None),
    ("CUIT", lambda i: i.cuit_facturacion or None),
    ("Marca", lambda i: i.marca.nombre if i.marca else None),
    ("Descripción", lambda i: i.descripcion or None),
    ("Período desde", lambda i: i.periodo_desde),
    ("Período hasta", lambda i: i.periodo_hasta),
    ("Cantidad", lambda i: _numero(i.cantidad)),
    ("Precio unitario", lambda i: _numero(i.precio_unitario)),
    ("Importe neto", lambda i: _numero(i.neto)),
    ("Alícuota IVA", lambda i: _numero(i.alicuota_iva)),
    ("IVA", lambda i: _numero(i.iva)),
    ("Total", lambda i: _numero(i.total)),
    ("Tipo de servicio", lambda i: i.get_tipo_servicio_display() or None),
    ("Tipo de soporte", lambda i: i.tipo_soporte or None),
    ("Gob/Priv", lambda i: i.sector.nombre if i.sector else None),
    ("Tipo de venta", lambda i: i.tipo_venta.nombre if i.tipo_venta else None),
    ("Notas", lambda i: i.notas or None),
    ("Orden de compra", lambda _i: None),
    ("Grupo de factura", lambda _i: None),
]


def planilla_xlsx(envio: EnvioFacturacion) -> bytes:
    """Planilla .xlsx del envío para Administración (HU-066, criterio 3), ordenada por cliente."""
    libro = Workbook()
    hoja = libro.worksheets[0]
    hoja.title = f"Facturación {envio.mes:%Y-%m}"
    hoja.append([titulo for titulo, _ in COLUMNAS_PLANILLA])
    items = envio.items.select_related("cliente", "marca", "sector", "tipo_venta")
    for item in sorted(items, key=lambda i: (i.cliente.nombre_visible if i.cliente else "", i.pk)):
        hoja.append([valor(item) for _, valor in COLUMNAS_PLANILLA])
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()
