# adapters/api/serializers/gobernanza_serializers.py
from rest_framework import serializers
from adapters.infrastructure.models import (
    EventoModel, AsistenciaModel, SocioModel, CatalogoRubroModel, 
    SolicitudJustificacionModel
)
from core.shared.enums import EstadoSolicitud

class EventoSerializer(serializers.ModelSerializer):
    """Serializer para gestión CRUD de Eventos (Mingas/Asambleas)"""
    
    class Meta:
        model = EventoModel
        fields = [
            'id', 'nombre', 'tipo', 'fecha', 
            'valor_multa',
            'estado', 'fecha_creacion'
        ]
        read_only_fields = ['fecha_creacion']

class AsistenciaItemSerializer(serializers.Serializer):
    """Item individual para la carga masiva de asistencia"""
    socio_id = serializers.IntegerField()
    estado = serializers.CharField(max_length=50) # VALIDAR CON ENUM EN USE CASE
    observacion = serializers.CharField(required=False, allow_blank=True)

class RegistroAsistenciaSerializer(serializers.Serializer):
    """Input para el endpoint de carga masiva"""
    evento_id = serializers.IntegerField()
    asistencias = AsistenciaItemSerializer(many=True)

class ResumenMultasSerializer(serializers.Serializer):
    """Output del proceso batch de multas"""
    multas_generadas = serializers.IntegerField()
    monto_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    mensaje = serializers.CharField()

class CrearSolicitudSerializer(serializers.Serializer):
    """Input para crear una solicitud de justificación"""
    asistencia_id = serializers.IntegerField()
    motivo = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()
    archivo_evidencia = serializers.FileField(required=False, allow_null=True)

class ResolucionSolicitudSerializer(serializers.Serializer):
    """Input para que el admin apruebe/rechace"""
    estado = serializers.ChoiceField(choices=[
        (EstadoSolicitud.APROBADA.value, 'APROBADA'),
        (EstadoSolicitud.RECHAZADA.value, 'RECHAZADA')
    ])
    observacion_admin = serializers.CharField(required=False, allow_blank=True)
