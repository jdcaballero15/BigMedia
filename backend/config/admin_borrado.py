"""Borrado de cargas erróneas desde el admin de Django, compartido entre apps (HU-006, criterio 4).

Solo el superusuario borra. Las FK de negocio son `PROTECT`, así que el admin no borra un registro
con actividad: muestra qué lo referencia. Cada borrado queda en auditoría, en la misma transacción.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.db import transaction
from django.db.models import Model, QuerySet
from django.http import HttpRequest

from apps.auditoria import services as auditoria_services

if TYPE_CHECKING:
    ModelAdminBase = admin.ModelAdmin[Any]
else:
    ModelAdminBase = admin.ModelAdmin


class BorradoAuditadoAdmin(ModelAdminBase):
    """La operación diaria inactiva o cancela; el superusuario borra una carga errónea auditada."""

    entidad: str

    def has_delete_permission(self, request: HttpRequest, _obj: Any = None) -> bool:
        return request.user.is_superuser

    def delete_model(self, request: HttpRequest, obj: Model) -> None:
        with transaction.atomic():
            auditoria_services.registrar_borrado(self.entidad, obj, request.user)
            super().delete_model(request, obj)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[Any]) -> None:
        with transaction.atomic():
            for obj in queryset:
                auditoria_services.registrar_borrado(self.entidad, obj, request.user)
            super().delete_queryset(request, queryset)


class SoloBorrarAdmin(BorradoAuditadoAdmin):
    """Ver y borrar: el alta y la edición van por la aplicación, que valida y audita."""

    def has_add_permission(self, _request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, _request: HttpRequest, _obj: Any = None) -> bool:
        return False
