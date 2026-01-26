from rest_framework import serializers
from core.domain.evento import TipoEvento
from adapters.infrastructure.models.evento_models import EventoModel, AsistenciaModel
from adapters.infrastructure.models.socio_model import SocioModel

class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoModel
        fields = '__all__'

class AsistenciaSerializer(serializers.ModelSerializer):
    socio_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = AsistenciaModel
        fields = ['id', 'evento', 'socio_id', 'socio_nombre', 'asistio', 'estado_justificacion', 'multa_factura', 'observacion']

    def get_socio_nombre(self, obj):
        try:
            # Optimización: si se usó select_related en la query, esto no golpea DB.
            # Como AsistenciaModel tiene socio FK (según mi última edición exitosa), accedemos a socio.
            # Pero en mi modelo definí 'socio' como FK.
            return f"{obj.socio.nombres} {obj.socio.apellidos}"
        except:
            return "Desconocido"

class CrearEventoRequestSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=200)
    tipo = serializers.ChoiceField(choices=[(e.value, e.value) for e in TipoEvento])
    fecha = serializers.DateField()
    valor_multa = serializers.DecimalField(max_digits=10, decimal_places=2)
    seleccion_socios = serializers.ChoiceField(choices=["TODOS", "BARRIO", "MANUAL"])
    barrio_id = serializers.IntegerField(required=False, allow_null=True)
    lista_socios_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_null=True)

    def validate(self, data):
        if data['seleccion_socios'] == 'BARRIO' and not data.get('barrio_id'):
            raise serializers.ValidationError("Debe especificar barrio_id si selecciona BARRIO.")
        if data['seleccion_socios'] == 'MANUAL' and not data.get('lista_socios_ids'):
            raise serializers.ValidationError("Debe especificar lista_socios_ids si selecciona MANUAL.")
        return data

class RegistrarAsistenciaRequestSerializer(serializers.Serializer):
    socios_ids = serializers.ListField(child=serializers.IntegerField())

class ProcesarJustificacionRequestSerializer(serializers.Serializer):
    asistencia_id = serializers.IntegerField()
    decision = serializers.ChoiceField(choices=["APROBADA", "RECHAZADA"])
    observacion = serializers.CharField(required=False, allow_blank=True)
