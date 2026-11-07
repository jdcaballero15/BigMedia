"""Reglas de negocio de campañas."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from apps.auditoria import services as auditoria_services
from apps.auditoria.models import RegistroAuditoria
from apps.clientes.models import Cliente, Contacto, Marca
from apps.inventario.models import Formato

from .models import Campania, LineaFormato, OrdenPublicidad

# Campo con el que la auditoría de la campaña registra adjuntar y dar de baja una orden.
CAMPO_AUDITORIA_OP = "orden_publicidad"


def validar_confirmacion(campania: Campania) -> None:
    """Para confirmar se exigen marca, cliente que factura y ambas fechas (RN-011)."""
    faltantes = []
    if campania.marca_id is None:
        faltantes.append("la marca")
    if campania.cliente_factura is None:
        faltantes.append("el cliente que factura")
    if campania.fecha_inicio is None or campania.fecha_fin is None:
        faltantes.append("las fechas")
    if faltantes:
        detalle = ", ".join(faltantes)
        raise ValidationError({"estado": f"Para confirmar falta cargar {detalle}."})


def estampar_cliente_anterior(marca: Marca, cliente_anterior: Cliente) -> None:
    """Las campañas de la marca sin cliente propio conservan el que las facturaba (HU-027, RN-014).

    Corre cuando la marca pasa a otro cliente, dentro de esa transacción. Toca todas las campañas,
    en cualquier estado; las que ya tienen cliente propio no cambian. Queda en auditoría como
    cambio del sistema.
    """
    campanias = Campania.objects.select_for_update().filter(
        marca=marca, cliente_facturacion__isnull=True
    )
    for campania in campanias:
        campania.cliente_facturacion = cliente_anterior
        campania.save(update_fields=["cliente_facturacion", "actualizado_en"])
        auditoria_services.registrar_cambios(
            "campania",
            campania.pk,
            {"cliente_facturacion": ""},
            {"cliente_facturacion": cliente_anterior.nombre_visible},
            None,
            origen=RegistroAuditoria.Origen.SISTEMA,
        )


def validar_contacto_de_interaccion(
    cliente: Cliente, contacto: Contacto | None, sin_cambios: bool
) -> None:
    """El contacto es del mismo cliente y está activo (HU-068 criterio 5).

    Un contacto que ya tenía la interacción se conserva aunque después se haya inactivado.
    """
    if contacto is None:
        return
    if contacto.cliente_id != cliente.pk:
        raise ValidationError({"contacto": "El contacto no es de ese cliente."})
    if not contacto.activo and not sin_cambios:
        raise ValidationError({"contacto": "Seleccioná un contacto activo."})


def validar_campania_de_interaccion(cliente: Cliente, campania: Campania | None) -> None:
    """La campaña la factura el cliente o es de una de sus marcas."""
    if campania is None:
        return
    facturador = campania.cliente_factura
    duenio_marca = campania.marca.cliente_id if campania.marca is not None else None
    if cliente.pk not in {getattr(facturador, "pk", None), duenio_marca}:
        raise ValidationError({"campania": "La campaña no es de ese cliente."})


def validar_marca_de_interaccion(
    cliente: Cliente, marca: Marca | None, campania: Campania | None, sin_cambios: bool
) -> None:
    """La marca es activa y del cliente, y la campaña, si hay, es de esa marca (RN-018).

    Una marca que ya tenía la interacción se conserva aunque después se haya inactivado.
    """
    if marca is None:
        return
    if marca.cliente_id != cliente.pk:
        raise ValidationError({"marca": "La marca no es de ese cliente."})
    if not marca.activo and not sin_cambios:
        raise ValidationError({"marca": "Seleccioná una marca activa."})
    if campania is not None and campania.marca_id != marca.pk:
        raise ValidationError({"campania": "La campaña no es de esa marca."})


def validar_linea_formato(
    campania: Campania,
    formato: Formato,
    activa: bool,
    actual: LineaFormato | None,
    formato_sin_cambios: bool,
) -> None:
    """Formato activo y sin repetir entre las líneas activas de la campaña (HU-055)."""
    if not formato.activo and not formato_sin_cambios:
        raise ValidationError({"formato": "Seleccioná un formato activo."})
    if not activa:
        return
    repetidas = LineaFormato.objects.filter(campania=campania, formato=formato, activa=True)
    if actual is not None:
        repetidas = repetidas.exclude(pk=actual.pk)
    if repetidas.exists():
        raise ValidationError({"formato": f"La campaña ya tiene una línea de {formato.nombre}."})


def validar_ordenes_publicidad(archivos: list[UploadedFile[bytes]]) -> None:
    """Solo PDF y hasta el tamaño máximo configurado (HU-069, criterio 4).

    Se valida todo antes de guardar nada: si un archivo falla, no se toca la base.
    """
    maximo = settings.CAMPANIAS_OP_MAX_MB
    for archivo in archivos:
        nombre = archivo.name or ""
        archivo.seek(0)
        es_pdf = nombre.lower().endswith(".pdf") and archivo.read(5) == b"%PDF-"
        archivo.seek(0)
        if not es_pdf:
            raise ValidationError({"ordenes_publicidad": "El archivo tiene que ser un PDF."})
        if (archivo.size or 0) > maximo * 1024 * 1024:
            raise ValidationError(
                {
                    "ordenes_publicidad": (
                        f"El PDF «{nombre}» supera el tamaño máximo de {maximo} MB."
                    )
                }
            )


def adjuntar_ordenes_publicidad(
    campania: Campania, archivos: list[UploadedFile[bytes]], usuario: AbstractBaseUser
) -> None:
    """Sube cada PDF al almacenamiento y lo registra en la campaña, auditado (HU-069)."""
    for archivo in archivos:
        nombre = (archivo.name or "")[:255]
        orden = OrdenPublicidad(
            campania=campania, nombre=nombre, tamanio=archivo.size or 0, subida_por_id=usuario.pk
        )
        orden.archivo.save(nombre, archivo, save=False)
        orden.save()
        auditoria_services.registrar_cambios(
            "campania", campania.pk, {CAMPO_AUDITORIA_OP: ""}, {CAMPO_AUDITORIA_OP: nombre}, usuario
        )


def dar_de_baja_orden_publicidad(orden_id: int, usuario: AbstractBaseUser) -> OrdenPublicidad:
    """Baja lógica: deja de estar vigente, pero el archivo y la fila quedan (HU-006, HU-069)."""
    with transaction.atomic():
        orden = OrdenPublicidad.objects.select_for_update().get(pk=orden_id)
        if not orden.activa:
            return orden
        orden.activa = False
        orden.dada_de_baja_por_id = usuario.pk
        orden.dada_de_baja_en = timezone.now()
        orden.save(update_fields=["activa", "dada_de_baja_por_id", "dada_de_baja_en"])
        auditoria_services.registrar_cambios(
            "campania",
            orden.campania_id,
            {CAMPO_AUDITORIA_OP: orden.nombre},
            {CAMPO_AUDITORIA_OP: ""},
            usuario,
        )
    return orden
