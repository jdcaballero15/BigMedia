from datetime import date, timedelta
from typing import cast

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from apps.auditoria import services as auditoria_services
from config.permisos import LecturaConSesionEdicionOperativo, LecturaSoloGerencia

from . import services
from .models import (
    GrupoFactura,
    ItemFacturacion,
    OrdenCompraPdf,
    Sector,
    TipoVenta,
)
from .serializers import (
    CostoDelItemSerializer,
    CostoElegibleSerializer,
    GrupoFacturaSerializer,
    ItemFacturacionSerializer,
    NuevoCostoSerializer,
)

# Cambios del ítem que quedan auditados (HU-007): importes y cliente. La baja se audita en
# `services.dar_de_baja`.
CAMPOS_AUDITADOS = ("neto", "alicuota_iva", "cliente_id")
# Tope de resultados del buscador de costos para elegir (HU-063).
LIMITE_ELEGIBLES = 50


def _primer_dia(valor: str | None, por_defecto: date) -> date:
    """Parsea un período `AAAA-MM` al primer día del mes; vacío usa el valor por defecto."""
    if not valor:
        return por_defecto
    try:
        return date.fromisoformat(f"{valor}-01")
    except ValueError as error:
        raise ValidationError({"periodo": "Formato de período inválido (AAAA-MM)."}) from error


def _ultimo_dia(primero: date) -> date:
    """Último día del mes del `primero` dado."""
    if primero.month == 12:
        return date(primero.year, 12, 31)
    return date(primero.year, primero.month + 1, 1) - timedelta(days=1)


class PorRubroView(APIView):
    """Reporte de ingresos y días-cupo por rubro de la marca (HU-050, criterio 1)."""

    permission_classes = [permissions.IsAuthenticated, LecturaSoloGerencia]
    reporte = staticmethod(services.reporte_por_rubro)

    def get(self, request: Request) -> Response:
        hoy = timezone.localdate()
        params = request.query_params
        desde = _primer_dia(params.get("desde"), date(hoy.year, 1, 1))
        hasta = _ultimo_dia(_primer_dia(params.get("hasta"), date(hoy.year, 12, 1)))
        if hasta < desde:
            raise ValidationError(
                {"hasta": "El período de fin no puede ser anterior al de inicio."}
            )
        return Response(self.reporte(desde, hasta))


class PorGrupoView(PorRubroView):
    """Reporte de ingresos y días-cupo por grupo económico de la marca (HU-050 criterio 2)."""

    reporte = staticmethod(services.reporte_por_grupo)


class IngresosView(APIView):
    """Reporte de ingresos por cliente y marca, repartidos por mes (HU-049)."""

    permission_classes = [permissions.IsAuthenticated, LecturaSoloGerencia]

    def get(self, request: Request) -> Response:
        hoy = timezone.localdate()
        params = request.query_params
        desde = _primer_dia(params.get("desde"), date(hoy.year, 1, 1))
        hasta = _ultimo_dia(_primer_dia(params.get("hasta"), date(hoy.year, 12, 1)))
        if hasta < desde:
            raise ValidationError(
                {"hasta": "El período de fin no puede ser anterior al de inicio."}
            )
        return Response(services.reporte_ingresos(desde, hasta))


def _id_positivo(valor: str, campo: str) -> int:
    if not valor.isdecimal() or int(valor) < 1:
        raise ValidationError({campo: "Debe ser un ID numérico positivo."})
    return int(valor)


def _mes(valor: str | None) -> date:
    """Parsea un mes `AAAA-MM` a su primer día."""
    if not valor:
        raise ValidationError({"mes": "Indicá el mes (AAAA-MM)."})
    try:
        return date.fromisoformat(f"{valor}-01")
    except ValueError as error:
        raise ValidationError({"mes": "Formato de mes inválido (AAAA-MM)."}) from error


def _usuario(request: Request) -> AbstractBaseUser:
    # El permiso exige sesión: el usuario siempre está autenticado.
    return cast(AbstractBaseUser, request.user)


def _a_drf(error: DjangoValidationError) -> ValidationError:
    return ValidationError(error.message_dict)


def _auditables(item: ItemFacturacion) -> dict[str, str]:
    valores = {campo: getattr(item, campo) for campo in CAMPOS_AUDITADOS}
    return {
        campo.removesuffix("_id"): "" if valor is None else str(valor)
        for campo, valor in valores.items()
    }


class ItemFacturacionViewSet(viewsets.ModelViewSet[ItemFacturacion]):
    """Ítems a facturar (HU-060, HU-061). Sin DELETE: se dan de baja y desde ahí no se ven."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    http_method_names = ["get", "post", "patch", "head", "options"]
    # El PDF de la OC se informa (nombre y tamaño) sin traer su contenido.
    queryset = (
        services.vigentes()
        .select_related(
            "cliente",
            "marca",
            "campania",
            "sector",
            "tipo_venta",
            "creado_por",
            "grupo",
            "orden_compra_pdf",
        )
        .defer("orden_compra_pdf__contenido")
        .prefetch_related(services.prefetch_costos_elegidos())
    )
    serializer_class = ItemFacturacionSerializer

    def _con_avisos(self, respuesta: Response) -> Response:
        """Suma el aviso de OC duplicada (HU-062, criterio 2): avisa, no bloquea."""
        item = ItemFacturacion.objects.get(pk=respuesta.data["id"])
        respuesta.data["avisos"] = {"orden_compra": services.ordenes_de_compra_duplicadas(item)}
        return respuesta

    def _releido(self, respuesta: Response) -> Response:
        """Vuelve a serializar el ítem guardado, con sus costos elegidos y su PDF actuales."""
        item = self.get_queryset().get(pk=respuesta.data["id"])
        respuesta.data = self.get_serializer(item).data
        return self._con_avisos(respuesta)

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        return self._releido(super().create(request, *args, **kwargs))

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        return self._releido(super().update(request, *args, **kwargs))

    def _guardar_extras(self, serializer: BaseSerializer[ItemFacturacion]) -> None:
        """Costos elegidos y PDF de la orden de publicidad, en la transacción del ítem."""
        item = cast(ItemFacturacion, serializer.instance)
        extras = cast(ItemFacturacionSerializer, serializer)
        usuario = _usuario(self.request)
        try:
            if extras.costos_pedidos is not None:
                services.elegir_costos(item.pk, extras.costos_pedidos, usuario)
            if extras.pdf_orden_publicidad is not None:
                services.guardar_pdf_orden_compra(item.pk, extras.pdf_orden_publicidad, usuario)
        except DjangoValidationError as error:
            raise _a_drf(error) from error

    def perform_create(self, serializer: BaseSerializer[ItemFacturacion]) -> None:
        # Si el PDF o un costo se rechaza, el ítem no se guarda a medias (HU-062, HU-063).
        with transaction.atomic():
            serializer.save(creado_por=self.request.user)
            self._guardar_extras(serializer)

    def perform_update(self, serializer: BaseSerializer[ItemFacturacion]) -> None:
        anteriores = _auditables(cast(ItemFacturacion, serializer.instance))
        # El cambio y su auditoría en la misma transacción: nunca un cambio sin su registro.
        with transaction.atomic():
            item = serializer.save()
            self._guardar_extras(serializer)
            services.recalcular_porcentuales(item)
            auditoria_services.registrar_cambios(
                "item_facturacion", item.pk, anteriores, _auditables(item), self.request.user
            )

    def get_queryset(self) -> QuerySet[ItemFacturacion]:
        queryset = super().get_queryset()
        if self.action not in ("list", "planilla"):
            return queryset
        # En el listado, el costo total viene sumado en la consulta (HU-063).
        queryset = services.con_costo_total(queryset)
        params = self.request.query_params
        if params.get("mes"):
            queryset = queryset.filter(mes=_mes(params["mes"]))
        for campo in ("cliente", "campania"):
            if params.get(campo):
                queryset = queryset.filter(**{f"{campo}_id": _id_positivo(params[campo], campo)})
        return queryset

    @action(detail=False, methods=["get"])
    def planilla(self, request: Request) -> HttpResponse:
        """«Descargar Excel» de la lista con sus filtros, sin los dados de baja (HU-070)."""
        items = self.get_queryset()
        mes = request.query_params.get("mes")
        periodo = _mes(mes) if mes else None
        nombre = f"facturacion-{periodo:%Y-%m}.xlsx" if periodo else "facturacion.xlsx"
        return HttpResponse(
            services.planilla_de_lista_xlsx(items, periodo),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
        )

    @action(detail=True, methods=["post"], url_path="quitar-del-grupo")
    def quitar_del_grupo(self, request: Request, pk: str) -> Response:
        """Deja el ítem independiente de su grupo de factura (HU-064, criterio 2)."""
        item = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            services.quitar_del_grupo(item.pk, _usuario(request))
        except DjangoValidationError as error:
            raise _a_drf(error) from error
        return Response(self.get_serializer(self.get_queryset().get(pk=item.pk)).data)

    @action(detail=True, methods=["post"], url_path="dar-de-baja")
    def dar_de_baja(self, request: Request, pk: str) -> Response:
        """Da de baja un ítem cargado por error, sin borrarlo (HU-060)."""
        item = get_object_or_404(self.get_queryset(), pk=pk)
        services.dar_de_baja(item.pk, _usuario(request))
        return Response({"id": item.pk})

    def _item_para_costos(self, pk: str) -> ItemFacturacion:
        return get_object_or_404(ItemFacturacion.objects.only("id", "campania_id"), pk=pk)

    @action(detail=True, methods=["get", "post"])
    def costos(self, request: Request, pk: str) -> Response:
        """Costos del ítem (HU-063): se listan todos, anulados incluidos, y se cargan."""
        item = self._item_para_costos(pk)
        if request.method == "GET":
            costos = services.costos_del_item(item)
            return Response(CostoDelItemSerializer(costos, many=True).data)
        datos = NuevoCostoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            costo = services.agregar_costo(item.pk, datos.validated_data, _usuario(request))
        except DjangoValidationError as error:
            raise _a_drf(error) from error
        return Response(CostoDelItemSerializer(costo).data, status=201)

    @action(detail=False, methods=["get"], url_path="costos-elegibles")
    def costos_elegibles(self, request: Request) -> Response:
        """Costos que se pueden elegir en un ítem, con buscador (HU-063, criterios 6 y 7)."""
        costos = services.costos_elegibles(request.query_params.get("q", ""))[:LIMITE_ELEGIBLES]
        return Response(CostoElegibleSerializer(costos, many=True).data)

    @action(detail=True, methods=["get"], url_path="costos/vinculables")
    def costos_vinculables(self, _request: Request, pk: str) -> Response:
        """Costos de reservas de cualquier campaña que se pueden vincular (HU-063)."""
        costos = services.costos_vinculables(self._item_para_costos(pk))
        return Response(CostoDelItemSerializer(costos, many=True).data)

    @action(detail=True, methods=["post"], url_path="costos/vincular")
    def vincular_costo(self, request: Request, pk: str) -> Response:
        """Vincula un costo de reserva de cualquier campaña, sin copiarlo (HU-063)."""
        item = self._item_para_costos(pk)
        costo_id = request.data.get("costo") if isinstance(request.data, dict) else None
        if not isinstance(costo_id, int) or isinstance(costo_id, bool) or costo_id < 1:
            raise ValidationError({"costo": "Indicá el costo a vincular."})
        try:
            costo = services.vincular_costo(item.pk, costo_id, _usuario(request))
        except DjangoValidationError as error:
            raise _a_drf(error) from error
        return Response(CostoDelItemSerializer(costo).data, status=201)

    @action(detail=True, methods=["post"], url_path=r"costos/(?P<costo_id>\d+)/anular")
    def anular_costo(self, request: Request, pk: str, costo_id: str) -> Response:
        """Anula con motivo un costo propio del ítem; deja de sumar (HU-063)."""
        item = self._item_para_costos(pk)
        get_object_or_404(services.costos_del_item(item), pk=costo_id)
        motivo = request.data.get("motivo") if isinstance(request.data, dict) else None
        try:
            costo = services.anular_costo(
                item.pk, int(costo_id), motivo if isinstance(motivo, str) else "", _usuario(request)
            )
        except DjangoValidationError as error:
            raise _a_drf(error) from error
        return Response(CostoDelItemSerializer(costo).data)

    @action(detail=False, methods=["get"])
    def totales(self, request: Request) -> Response:
        """Neto, IVA y total del mes, sin los anulados (HU-065, criterio 3)."""
        return Response(services.totales_del_mes(_mes(request.query_params.get("mes"))))


class OrdenCompraPdfView(APIView):
    """PDF de la orden de compra del ítem (HU-062): se sube, se abre y se quita."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    parser_classes = [MultiPartParser]

    def _item(self, pk: int) -> ItemFacturacion:
        return get_object_or_404(ItemFacturacion.objects.only("id"), pk=pk)

    def get(self, _request: Request, pk: int) -> HttpResponse:
        pdf = get_object_or_404(OrdenCompraPdf, item=self._item(pk))
        return HttpResponse(
            bytes(pdf.contenido),
            content_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{pdf.nombre}"'},
        )

    def put(self, request: Request, pk: int) -> Response:
        item = self._item(pk)
        archivo = request.FILES.get("archivo")
        try:
            pdf = services.guardar_pdf_orden_compra(item.pk, archivo, _usuario(request))
        except DjangoValidationError as error:
            raise _a_drf(error) from error
        return Response({"nombre": pdf.nombre, "tamanio": pdf.tamanio})

    def delete(self, request: Request, pk: int) -> Response:
        item = self._item(pk)
        try:
            quitado = services.quitar_pdf_orden_compra(item.pk, _usuario(request))
        except DjangoValidationError as error:
            raise _a_drf(error) from error
        if not quitado:
            raise Http404
        return Response(status=204)


class GrupoFacturaViewSet(viewsets.GenericViewSet[GrupoFactura]):
    """Grupos de factura (HU-064): se crean agrupando ítems; quitar es una acción del ítem."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]
    queryset = GrupoFactura.objects.prefetch_related("items")
    serializer_class = GrupoFacturaSerializer

    def create(self, request: Request) -> Response:
        ids = request.data.get("items") if isinstance(request.data, dict) else None
        validos = isinstance(ids, list) and all(
            isinstance(pk, int) and not isinstance(pk, bool) and pk > 0 for pk in ids
        )
        if not validos:
            raise ValidationError({"items": "Indicá la lista de ítems a agrupar."})
        try:
            grupo = services.agrupar(cast(list[int], ids), _usuario(request))
        except DjangoValidationError as error:
            raise _a_drf(error) from error
        return Response(self.get_serializer(self.get_queryset().get(pk=grupo.pk)).data, status=201)


class CatalogosFacturacionView(APIView):
    """Sectores (Gob/Priv) y tipos de venta (F/V) activos (RN-023)."""

    permission_classes = [permissions.IsAuthenticated, LecturaConSesionEdicionOperativo]

    def get(self, _request: Request) -> Response:
        return Response(
            {
                "sectores": list(Sector.objects.filter(activo=True).values("id", "nombre")),
                "tipos_venta": list(TipoVenta.objects.filter(activo=True).values("id", "nombre")),
            }
        )
