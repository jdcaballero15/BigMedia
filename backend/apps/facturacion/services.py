"""Reglas de facturación: ítems a facturar (HU-060 a HU-066) y reportes de ingresos."""

from __future__ import annotations

import io
import logging
import smtplib
from datetime import date
from decimal import Decimal
from functools import partial
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Count, DecimalField, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from openpyxl import Workbook

from apps.auditoria import services as auditoria_services
from apps.costos import services as costos_services
from apps.costos.models import Costo
from apps.reservas.models import MESES_ABREV, Reserva
from apps.reservas.services import reparto_por_mes

from .models import (
    CostoDeItem,
    EnvioFacturacion,
    GrupoFactura,
    ItemFacturacion,
    OrdenCompraPdf,
    al_centavo,
)

CERO = Decimal("0.00")

logger = logging.getLogger(__name__)


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

    Marca sin rubro → "Sin rubro". Las cuentas están en `_corte_por_marca`.
    """
    return _corte_por_marca(desde, hasta, "rubro", "Sin rubro")


def reporte_por_grupo(desde: date, hasta: date) -> dict[str, Any]:
    """Ingresos y días-cupo por grupo económico de la marca (HU-050 criterio 2, RN-016).

    Marca sin grupo → "Sin grupo". Las cuentas están en `_corte_por_marca`.
    """
    return _corte_por_marca(desde, hasta, "grupo", "Sin grupo")


def _corte_por_marca(desde: date, hasta: date, campo: str, sin_valor: str) -> dict[str, Any]:
    """Acumula ingresos y días-cupo según un catálogo de la marca (`rubro` o `grupo`).

    Para cada reserva que ocupa cupo y se solapa con `[desde, hasta]`, acumula:
    - ingresos: suma del reparto por mes (HU-051) dentro del período.
    - días-cupo: días de solape de la reserva con el período (una reserva = un cupo, RN-004).
    Agrupa por `marca.<campo>` de la campaña; sin valor (o sin marca) → `sin_valor`. Ordena por
    ingresos descendente. Los importes salen como string de 2 decimales.
    """
    claves = {p["mes"] for p in _meses_periodo(desde, hasta)}
    reservas = Reserva.objects.filter(
        estado__in=Reserva.ESTADOS_QUE_OCUPAN, fecha_inicio__lte=hasta, fecha_fin__gte=desde
    ).select_related(f"campania__marca__{campo}")

    acumulador: dict[int | None, dict[str, Any]] = {}
    for reserva in reservas:
        marca = reserva.campania.marca
        valor = getattr(marca, campo) if marca is not None else None
        clave = valor.pk if valor is not None else None
        nombre = valor.nombre if valor is not None else sin_valor

        montos = {i["mes"]: i["monto"] for i in reparto_por_mes(reserva) if i["mes"] in claves}
        bucket = acumulador.setdefault(
            clave, {campo: clave, "nombre": nombre, "ingresos": CERO, "dias_cupo": 0}
        )
        bucket["ingresos"] = bucket["ingresos"] + sum(montos.values(), CERO)
        bucket["dias_cupo"] = bucket["dias_cupo"] + _dias_solape(
            reserva.fecha_inicio, reserva.fecha_fin, desde, hasta
        )

    total_ingresos = sum((b["ingresos"] for b in acumulador.values()), CERO)
    total_dias_cupo = sum(b["dias_cupo"] for b in acumulador.values())
    filas = sorted(acumulador.values(), key=lambda b: b["ingresos"], reverse=True)
    return {
        f"{campo}s": [
            {
                campo: b[campo],
                "nombre": b["nombre"],
                "ingresos": _fmt(b["ingresos"]),
                "dias_cupo": b["dias_cupo"],
                "porcentaje_ocupacion": (
                    round(b["dias_cupo"] / total_dias_cupo * 100, 1) if total_dias_cupo else 0.0
                ),
            }
            for b in filas
        ],
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
# Fuera de Borrador solo se cambia el estado (y el número al facturar); para corregir un Enviado
# se lo reabre (HU-067).
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
    """Neto, IVA, total, costos y neto final del mes, sin los anulados (HU-065, HU-063)."""
    items = ItemFacturacion.objects.filter(mes=mes).exclude(estado=ItemFacturacion.Estado.ANULADO)
    fila = items.aggregate(
        cantidad=Count("id"), neto=Sum("neto"), iva=Sum("iva"), total=Sum("total")
    )
    costos = (
        Costo.objects.filter(item_vinculado__item__in=items, anulado=False).aggregate(
            total=Sum("monto")
        )["total"]
        or CERO
    )
    neto = fila["neto"] or CERO
    return {
        "mes": mes.strftime("%Y-%m"),
        "cantidad": fila["cantidad"],
        **{campo: str(al_centavo(fila[campo] or CERO)) for campo in ("neto", "iva", "total")},
        "costos": str(al_centavo(costos)),
        "neto_final": str(al_centavo(neto - costos)),
    }


# --- Costos del ítem y neto final (HU-063) ---


def con_costo_total(items: QuerySet[ItemFacturacion]) -> QuerySet[ItemFacturacion]:
    """Anota `costo_total_anotado`: la suma de los costos no anulados de cada ítem."""
    return items.annotate(
        costo_total_anotado=Coalesce(
            Sum("costos__costo__monto", filter=Q(costos__costo__anulado=False)),
            Value(CERO),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )


def costo_total(item: ItemFacturacion) -> Decimal:
    """Suma de los costos no anulados del ítem (usa la anotación si la trae)."""
    anotado: Decimal | None = getattr(item, "costo_total_anotado", None)
    if anotado is not None:
        return al_centavo(anotado)
    total = Costo.objects.filter(item_vinculado__item=item, anulado=False).aggregate(
        total=Sum("monto")
    )["total"]
    return al_centavo(total or CERO)


def neto_final(item: ItemFacturacion) -> Decimal | None:
    """Importe neto menos los costos del ítem; None si el ítem no tiene neto."""
    if item.neto is None:
        return None
    return al_centavo(item.neto) - costo_total(item)


def monto_por_porcentaje(neto: Decimal | None, porcentaje: Decimal) -> Decimal:
    """Porcentaje del neto, redondeado al centavo; sin neto da 0 (HU-063, criterio 1)."""
    if neto is None:
        return CERO
    return al_centavo(neto * porcentaje / Decimal(100))


def costos_del_item(item: ItemFacturacion) -> QuerySet[Costo]:
    return (
        Costo.objects.filter(item_vinculado__item=item)
        .select_related("proveedor", "reserva__cartel")
        .order_by("item_vinculado__id")
    )


def costos_vinculables(item: ItemFacturacion) -> QuerySet[Costo]:
    """Costos no anulados de reservas de la campaña del ítem que no están en otro ítem."""
    if item.campania_id is None:
        return Costo.objects.none()
    return (
        Costo.objects.filter(
            reserva__campania_id=item.campania_id, anulado=False, item_vinculado__isnull=True
        )
        .select_related("proveedor", "reserva__cartel")
        .order_by("id")
    )


def _describir(costo: Costo) -> str:
    return f"{costo.get_tipo_display()} {costo.monto:.2f}"


def _auditar_costo(
    item: ItemFacturacion, antes: str, despues: str, usuario: AbstractBaseUser
) -> None:
    auditoria_services.registrar_cambios(
        "item_facturacion", item.pk, {"costos": antes}, {"costos": despues}, usuario
    )


def _validar_importe(datos: dict[str, Any]) -> None:
    if (datos.get("monto") is None) == (datos.get("porcentaje") is None):
        raise ValidationError({"monto": "Cargá un monto fijo o un porcentaje del neto, uno solo."})


def agregar_costo(item_id: int, datos: dict[str, Any], usuario: AbstractBaseUser) -> Costo:
    """Carga un costo propio del ítem en Borrador, fijo o en porcentaje del neto (HU-063).

    Crea el costo sin reserva y su vínculo en la misma transacción, y lo deja auditado.
    """
    _validar_importe(datos)
    if datos.get("proveedor") is not None:
        costos_services.validar_proveedor_activo(datos["proveedor"])
    with transaction.atomic():
        item = ItemFacturacion.objects.select_for_update().get(pk=item_id)
        _exigir_borrador(item, "cargar costos")
        porcentaje = datos.get("porcentaje")
        costo = Costo.objects.create(
            tipo=datos["tipo"],
            proveedor_id=datos.get("proveedor"),
            destinatario=datos.get("destinatario", "").strip(),
            porcentaje=porcentaje,
            monto=(
                monto_por_porcentaje(item.neto, porcentaje)
                if porcentaje is not None
                else datos["monto"]
            ),
            fecha=timezone.localdate(),
        )
        CostoDeItem.objects.create(item=item, costo=costo, vinculado_por_id=usuario.pk)
        _auditar_costo(item, "", f"Alta: {_describir(costo)}", usuario)
    return costo


def vincular_costo(item_id: int, costo_id: int, usuario: AbstractBaseUser) -> Costo:
    """Vincula al ítem un costo de una reserva de su campaña, sin copiarlo (HU-063, criterio 4)."""
    with transaction.atomic():
        item = ItemFacturacion.objects.select_for_update().get(pk=item_id)
        _exigir_borrador(item, "cargar costos")
        if item.campania_id is None:
            raise ValidationError(
                {"campania": "Solo se vinculan costos de reserva a un ítem con campaña."}
            )
        costo = costos_vinculables(item).select_for_update(of=("self",)).filter(pk=costo_id).first()
        if costo is None:
            raise ValidationError(
                {"costo": "El costo no es de una reserva de la campaña o ya está en otro ítem."}
            )
        try:
            with transaction.atomic():
                CostoDeItem.objects.create(item=item, costo=costo, vinculado_por_id=usuario.pk)
        except IntegrityError as error:
            # Otro ítem lo vinculó a la vez: la unicidad del costo lo frena.
            raise ValidationError({"costo": "El costo ya está en otro ítem."}) from error
        _auditar_costo(item, "", f"Vínculo: {_describir(costo)}", usuario)
    return costo


def anular_costo(item_id: int, costo_id: int, motivo: str, usuario: AbstractBaseUser) -> Costo:
    """Anula con motivo un costo propio del ítem: deja de sumar y no se borra (HU-063).

    Un costo de reserva vinculado se anula desde Costos, porque también es de la reserva.
    """
    motivo = motivo.strip()
    if not motivo:
        raise ValidationError({"motivo": "Indicá el motivo de la anulación."})
    with transaction.atomic():
        item = ItemFacturacion.objects.select_for_update().get(pk=item_id)
        _exigir_borrador(item, "anular costos")
        costo = Costo.objects.select_for_update().get(item_vinculado__item=item, pk=costo_id)
        if costo.reserva_id is not None:
            raise ValidationError({"costo": "Es un costo de una reserva: anulalo desde Costos."})
        if costo.anulado:
            raise ValidationError({"costo": "El costo ya está anulado."})
        costo.anulado = True
        costo.motivo_anulacion = motivo[:200]
        costo.save(update_fields=["anulado", "motivo_anulacion", "actualizado_en"])
        _auditar_costo(item, _describir(costo), f"Anulado: {motivo[:200]}", usuario)
    return costo


def recalcular_porcentuales(item: ItemFacturacion) -> None:
    """Vuelve a calcular los costos en porcentaje con el neto actual (HU-063, criterio 3)."""
    for costo in Costo.objects.select_for_update().filter(item_vinculado__item=item):
        if costo.porcentaje is None:
            continue
        nuevo = monto_por_porcentaje(item.neto, costo.porcentaje)
        if nuevo != costo.monto:
            costo.monto = nuevo
            costo.save(update_fields=["monto", "actualizado_en"])


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
            _marcar_enviado(item, usuario)
    return envio, incompletos


def _marcar_enviado(item: ItemFacturacion, usuario: AbstractBaseUser) -> None:
    """Pasa el ítem a Enviado; si estaba reabierto, lo marca reenviado y avisa (HU-067)."""
    item.estado = ItemFacturacion.Estado.ENVIADO
    item.reenviado = item.reabierto_en is not None
    item.save(update_fields=["estado", "reenviado", "actualizado_en"])
    auditoria_services.registrar_cambios(
        "item_facturacion",
        item.pk,
        {"estado": ItemFacturacion.Estado.BORRADOR.value},
        {"estado": ItemFacturacion.Estado.ENVIADO.value},
        usuario,
    )
    if item.reenviado:
        asunto, cuerpo = _aviso_de_reenvio(item)
        transaction.on_commit(partial(avisar_a_administracion, asunto, cuerpo))


def ordenes_de_compra_duplicadas(item: ItemFacturacion) -> list[dict[str, Any]]:
    """Otros ítems no anulados con el mismo número de OC (HU-062, criterio 2). Solo avisa."""
    numero = item.orden_compra_numero.strip()
    if not numero:
        return []
    coincidentes = (
        ItemFacturacion.objects.filter(orden_compra_numero__iexact=numero)
        .exclude(pk=item.pk)
        .exclude(estado=ItemFacturacion.Estado.ANULADO)
        .order_by("id")
        .values_list("pk", "descripcion")
    )
    return [{"id": pk, "descripcion": desc or "Sin descripción"} for pk, desc in coincidentes]


def _exigir_borrador(item: ItemFacturacion, que: str) -> None:
    if item.estado != ItemFacturacion.Estado.BORRADOR:
        raise ValidationError({"estado": f"Solo se puede {que} de un ítem en Borrador."})


def validar_pdf(archivo: UploadedFile[bytes] | None) -> UploadedFile[bytes]:
    """Solo PDF, hasta el tamaño máximo configurado (HU-062, criterio 3)."""
    if archivo is None:
        raise ValidationError({"archivo": "Adjuntá el PDF de la orden de compra."})
    archivo.seek(0)
    es_pdf = (archivo.name or "").lower().endswith(".pdf") and archivo.read(5) == b"%PDF-"
    if not es_pdf:
        raise ValidationError({"archivo": "El archivo tiene que ser un PDF."})
    maximo = settings.FACTURACION_OC_MAX_MB
    if (archivo.size or 0) > maximo * 1024 * 1024:
        raise ValidationError({"archivo": f"El PDF supera el tamaño máximo de {maximo} MB."})
    archivo.seek(0)
    return archivo


def _nombre_pdf(item: ItemFacturacion) -> str:
    pdf = OrdenCompraPdf.objects.filter(item=item).only("nombre").first()
    return pdf.nombre if pdf is not None else ""


def guardar_pdf_orden_compra(
    item_id: int, archivo: UploadedFile[bytes] | None, usuario: AbstractBaseUser
) -> OrdenCompraPdf:
    """Adjunta (o reemplaza) el PDF de la OC de un ítem en Borrador, auditado (HU-062)."""
    with transaction.atomic():
        item = ItemFacturacion.objects.select_for_update().get(pk=item_id)
        _exigir_borrador(item, "cambiar la orden de compra")
        archivo = validar_pdf(archivo)
        anterior = _nombre_pdf(item)
        nombre = (archivo.name or "orden-de-compra.pdf")[-255:]
        pdf, _ = OrdenCompraPdf.objects.update_or_create(
            item=item,
            defaults={
                "nombre": nombre,
                "tamanio": archivo.size or 0,
                "contenido": archivo.read(),
                "subido_por_id": usuario.pk,
            },
        )
        auditoria_services.registrar_cambios(
            "item_facturacion",
            item.pk,
            {"orden_compra_pdf": anterior},
            {"orden_compra_pdf": nombre},
            usuario,
        )
    return pdf


def quitar_pdf_orden_compra(item_id: int, usuario: AbstractBaseUser) -> bool:
    """Saca el PDF de la OC de un ítem en Borrador, auditado. Devuelve False si no tenía."""
    with transaction.atomic():
        item = ItemFacturacion.objects.select_for_update().get(pk=item_id)
        _exigir_borrador(item, "cambiar la orden de compra")
        anterior = _nombre_pdf(item)
        if not anterior:
            return False
        OrdenCompraPdf.objects.filter(item=item).delete()
        auditoria_services.registrar_cambios(
            "item_facturacion",
            item.pk,
            {"orden_compra_pdf": anterior},
            {"orden_compra_pdf": ""},
            usuario,
        )
    return True


def _mes_agrupable(ids: list[int], items: list[ItemFacturacion]) -> date:
    """Valida que los ítems se puedan agrupar y devuelve su mes común."""
    if len(items) != len(ids):
        raise ValidationError({"items": "Alguno de los ítems no existe."})
    if any(item.estado != ItemFacturacion.Estado.BORRADOR for item in items):
        raise ValidationError({"items": "Solo se agrupan ítems en Borrador."})
    meses = {item.mes for item in items}
    mes = meses.pop() if len(meses) == 1 else None
    if mes is None:
        raise ValidationError({"items": "Los ítems de un grupo tienen que ser del mismo mes."})
    return mes


def agrupar(ids: list[int], usuario: AbstractBaseUser) -> GrupoFactura:
    """Pone los ítems en un mismo grupo de factura (HU-064, criterio 1).

    Si alguno ya tiene grupo, los demás se suman a ese; dos grupos distintos se rechazan.
    """
    ids = sorted(set(ids))
    if len(ids) < 2:
        raise ValidationError({"items": "Elegí al menos dos ítems para agrupar."})
    with transaction.atomic():
        items = list(ItemFacturacion.objects.select_for_update().filter(pk__in=ids).order_by("id"))
        mes = _mes_agrupable(ids, items)
        existentes = {item.grupo_id for item in items if item.grupo_id is not None}
        if len(existentes) > 1:
            raise ValidationError({"items": "Los ítems ya están en dos grupos distintos."})
        if existentes:
            grupo = GrupoFactura.objects.get(pk=existentes.pop())
        else:
            grupo = GrupoFactura.objects.create(mes=mes, creado_por_id=usuario.pk)
        for item in items:
            if item.grupo_id == grupo.pk:
                continue
            item.grupo = grupo
            item.save(update_fields=["grupo", "actualizado_en"])
            auditoria_services.registrar_cambios(
                "item_facturacion", item.pk, {"grupo": ""}, {"grupo": grupo.codigo}, usuario
            )
    return grupo


def quitar_del_grupo(item_id: int, usuario: AbstractBaseUser) -> ItemFacturacion:
    """Deja el ítem independiente de su grupo de factura (HU-064, criterio 2)."""
    with transaction.atomic():
        item = ItemFacturacion.objects.select_for_update().get(pk=item_id)
        if item.grupo_id is None:
            raise ValidationError({"grupo": "El ítem no está en un grupo de factura."})
        _exigir_borrador(item, "cambiar el grupo de factura")
        anterior = f"G-{item.grupo_id}"
        item.grupo = None
        item.save(update_fields=["grupo", "actualizado_en"])
        auditoria_services.registrar_cambios(
            "item_facturacion", item.pk, {"grupo": anterior}, {"grupo": ""}, usuario
        )
    return item


def _numero(valor: Decimal | None) -> float | None:
    return float(valor) if valor is not None else None


# Columnas de la planilla para Administración (RN-024, provisoria hasta tener la planilla real):
# las de hoy y, al final, las nuevas: orden de compra (HU-062), grupo de factura (HU-064), y
# costos y neto final (HU-063), y la marca de reenviado (HU-067).
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
    ("Orden de compra", lambda i: i.orden_compra_numero or None),
    ("Fecha OC", lambda i: i.orden_compra_fecha),
    ("Grupo de factura", lambda i: i.grupo.codigo if i.grupo else None),
    ("Costos", lambda i: _numero(costo_total(i))),
    ("Neto final", lambda i: _numero(neto_final(i))),
    ("Reenviado", lambda i: "Sí" if i.reenviado else None),
]


def _filas_agrupadas(items: list[ItemFacturacion]) -> list[ItemFacturacion]:
    """Por cliente, y los ítems de un grupo juntos donde aparece el primero (HU-064, criterio 3)."""
    ordenados = sorted(items, key=lambda i: (i.cliente.nombre_visible if i.cliente else "", i.pk))
    filas: list[ItemFacturacion] = []
    grupos_puestos: set[int] = set()
    for item in ordenados:
        if item.grupo_id is None:
            filas.append(item)
        elif item.grupo_id not in grupos_puestos:
            grupos_puestos.add(item.grupo_id)
            filas.extend(i for i in ordenados if i.grupo_id == item.grupo_id)
    return filas


def planilla_xlsx(envio: EnvioFacturacion) -> bytes:
    """Planilla .xlsx del envío para Administración (HU-066, criterio 3), por cliente y grupo."""
    libro = Workbook()
    hoja = libro.worksheets[0]
    hoja.title = f"Facturación {envio.mes:%Y-%m}"
    hoja.append([titulo for titulo, _ in COLUMNAS_PLANILLA])
    items = con_costo_total(
        envio.items.select_related("cliente", "marca", "sector", "tipo_venta", "grupo")
    )
    for item in _filas_agrupadas(list(items)):
        hoja.append([valor(item) for _, valor in COLUMNAS_PLANILLA])
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


# --- Reabrir un ítem enviado y avisar a Administración (HU-067, RN-022) ---


def _como_texto(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float):
        return f"{valor:.2f}"
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def valores_de_planilla(item: ItemFacturacion) -> dict[str, str]:
    """Lo que Administración ve del ítem en la planilla, como texto, para comparar."""
    return {
        titulo: _como_texto(valor(item))
        for titulo, valor in COLUMNAS_PLANILLA
        if titulo != "Reenviado"
    }


def avisar_a_administracion(asunto: str, cuerpo: str) -> None:
    """Manda el aviso por correo (RN-022). Si no hay dirección o falla, lo deja en el log."""
    destino = settings.FACTURACION_CORREO_ADMINISTRACION
    if not destino:
        logger.warning(
            "Aviso a Administración sin enviar (falta FACTURACION_CORREO_ADMINISTRACION): %s",
            asunto,
        )
        return
    try:
        send_mail(asunto, cuerpo, None, [destino])
    except (smtplib.SMTPException, OSError):
        logger.exception("No se pudo enviar el aviso a Administración: %s", asunto)


def _titulo(item: ItemFacturacion) -> str:
    return f"Ítem #{item.pk} · {item.descripcion or 'Sin descripción'}"


def _reapertura(item: ItemFacturacion) -> str:
    cuando = timezone.localtime(item.reabierto_en).strftime("%d/%m/%Y %H:%M")
    quien = item.reabierto_por.get_username() if item.reabierto_por else "—"
    return f"Reabierto por {quien} el {cuando}.\nMotivo: {item.motivo_reapertura}"


def _aviso_de_reapertura(item: ItemFacturacion) -> tuple[str, str]:
    mes = item.mes.strftime("%Y-%m") if item.mes else "sin mes"
    cuerpo = (
        f"{_titulo(item)} (mes {mes}) se reabrió para corregirlo.\n"
        f"{_reapertura(item)}\n\n"
        "No lo facturen hasta que se reenvíe: les va a llegar otro aviso con lo que cambió."
    )
    return f"Ítem #{item.pk} reabierto: no facturar hasta el reenvío", cuerpo


def _aviso_de_reenvio(item: ItemFacturacion) -> tuple[str, str]:
    antes = item.valores_al_reabrir
    ahora = valores_de_planilla(item)
    cambios = [
        f"- {campo}: {antes.get(campo, '') or '(vacío)'} → {valor or '(vacío)'}"
        for campo, valor in ahora.items()
        if antes.get(campo, "") != valor
    ]
    detalle = "\n".join(cambios) if cambios else "Sin cambios desde la reapertura."
    cuerpo = f"{_titulo(item)} se reenvió a facturar.\n{_reapertura(item)}\n\nCambios:\n{detalle}"
    return f"Ítem #{item.pk} reenviado a facturar", cuerpo


def reabrir(item_id: int, motivo: str, usuario: AbstractBaseUser) -> ItemFacturacion:
    """Vuelve a Borrador un ítem Enviado para corregirlo, con motivo y auditado (HU-067).

    Guarda cómo estaba en la planilla para avisar qué cambió al reenviarlo. El aviso sale al
    confirmarse la transacción.
    """
    motivo = motivo.strip()[:200]
    if not motivo:
        raise ValidationError({"motivo": "Indicá el motivo de la reapertura."})
    with transaction.atomic():
        item = ItemFacturacion.objects.select_for_update().get(pk=item_id)
        if item.estado != ItemFacturacion.Estado.ENVIADO:
            raise ValidationError({"estado": "Solo se reabre un ítem Enviado a facturar."})
        anteriores = {"estado": item.estado, "motivo_reapertura": item.motivo_reapertura}
        item.valores_al_reabrir = valores_de_planilla(item)
        item.estado = ItemFacturacion.Estado.BORRADOR
        item.reabierto_en = timezone.now()
        item.reabierto_por_id = usuario.pk
        item.motivo_reapertura = motivo
        item.reenviado = False
        item.save()
        auditoria_services.registrar_cambios(
            "item_facturacion",
            item.pk,
            anteriores,
            {"estado": item.estado, "motivo_reapertura": motivo},
            usuario,
        )
        asunto, cuerpo = _aviso_de_reapertura(item)
        transaction.on_commit(partial(avisar_a_administracion, asunto, cuerpo))
    return item
