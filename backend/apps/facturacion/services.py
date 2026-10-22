"""Reportes de facturación (solo lectura)."""

from datetime import date
from decimal import Decimal
from typing import Any

from apps.reservas.models import MESES_ABREV, Reserva
from apps.reservas.services import reparto_por_mes

CERO = Decimal("0.00")


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
