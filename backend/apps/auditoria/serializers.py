"""Serializers de auditoría."""

from rest_framework import serializers

from .models import RegistroAuditoria


class RegistroAuditoriaSerializer(serializers.ModelSerializer[RegistroAuditoria]):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAuditoria
        fields = [
            "id",
            "entidad",
            "entidad_id",
            "campo",
            "valor_anterior",
            "valor_nuevo",
            "usuario",
            "usuario_nombre",
            "origen",
            "momento",
        ]

    def get_usuario_nombre(self, obj: RegistroAuditoria) -> str:
        if obj.usuario is None:
            return "Sistema"
        return str(obj.usuario.get_username())
