# adapters/api/serializers/servicio_serializers.py
from rest_framework import serializers
from adapters.infrastructure.models import (
    ServicioModel, OrdenTrabajoModel, EvidenciaOrdenTrabajoModel
)

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicioModel
        fields = ['id', 'socio', 'medidor', 'direccion', 'estado'] # Ajustar campos según modelo real

class EvidenciaOrdenSerializer(serializers.ModelSerializer):
    archivo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EvidenciaOrdenTrabajoModel
        fields = ['id', 'archivo', 'archivo_url', 'descripcion', 'fecha_subida']

    def get_archivo_url(self, obj):
        return obj.archivo.url if obj.archivo else None

class OrdenTrabajoSerializer(serializers.ModelSerializer):
    evidencias = EvidenciaOrdenSerializer(many=True, read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = OrdenTrabajoModel
        fields = [
            'id', 'servicio', 'tipo', 'tipo_display', 'estado', 'estado_display',
            'fecha_generacion', 'fecha_ejecucion', 'observacion_tecnico',
            'operador_asignado', 'evidencias'
        ]
        read_only_fields = ['fecha_generacion', 'fecha_ejecucion', 'tipo', 'servicio']

class CompletarOrdenSerializer(serializers.Serializer):
    archivo_evidencia = serializers.FileField(required=True)
    observacion = serializers.CharField(required=False, allow_blank=True)

class ProcesarCortesBatchSerializer(serializers.Serializer):
    confirmar = serializers.BooleanField(required=True) # Simple seguridad
