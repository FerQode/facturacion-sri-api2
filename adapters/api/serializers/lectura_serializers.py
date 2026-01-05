# adapters/api/serializers/lectura_serializers.py
from rest_framework import serializers
from adapters.infrastructure.models import LecturaModel
from core.use_cases.registrar_lectura_uc import RegistrarLecturaDTO

class RegistrarLecturaSerializer(serializers.Serializer):
    """
    Valida el JSON de ENTRADA para registrar una lectura.
    """
    medidor_id = serializers.IntegerField(required=True)
    lectura_actual = serializers.DecimalField(required=True, min_value=0, max_digits=12, decimal_places=2, source='lectura_actual_m3')
    # Nota: Aceptamos 'lectura_actual_m3' o 'lectura_actual' en el JSON, 
    # pero internamente lo mapeamos al DTO.
    fecha_lectura = serializers.DateField(required=True)
    observacion = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def to_dto(self) -> RegistrarLecturaDTO:
        return RegistrarLecturaDTO(
            medidor_id=self.validated_data['medidor_id'],
            valor=self.validated_data['lectura_actual_m3'], # DRF usa el source para el key interno
            observacion=self.validated_data.get('observacion')
        )

class LecturaResponseSerializer(serializers.ModelSerializer):
    """
    Serializador de SALIDA para una lectura recién creada.
    """
    medidor_id = serializers.IntegerField()
    consumo_del_mes = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, source='consumo_del_mes_m3'
    )
    lectura_anterior = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = LecturaModel
        fields = [
            'id', 'medidor_id', 'fecha', 'valor', 
            'lectura_anterior', 'consumo_del_mes', 
            'observacion', 'esta_facturada'
        ]

# --- NUEVO: SERIALIZER PARA HISTORIAL (Prioridad 1.3) ---
class LecturaHistorialSerializer(serializers.ModelSerializer):
    """
    Serializer de Salida Plano para Tablas del Frontend.
    Ruta: Lectura -> Medidor -> Terreno -> Socio
    """
    id = serializers.IntegerField(read_only=True)
    fecha = serializers.DateField(format="%Y-%m-%d")
    lectura_actual = serializers.DecimalField(source='valor', max_digits=12, decimal_places=2)
    lectura_anterior = serializers.DecimalField(max_digits=12, decimal_places=2)
    consumo = serializers.DecimalField(source='consumo_del_mes', max_digits=12, decimal_places=2)
    estado = serializers.SerializerMethodField()
    
    # Flattening (Aplanado de datos)
    medidor_codigo = serializers.CharField(source='medidor.codigo', default="S/N")
    socio_nombre = serializers.SerializerMethodField()

    class Meta:
        model = LecturaModel
        fields = [
            'id', 'fecha', 'medidor_codigo', 'socio_nombre', 
            'lectura_anterior', 'lectura_actual', 'consumo', 'estado'
        ]

    def get_estado(self, obj):
        return "Facturada" if obj.esta_facturada else "Registrada"

    def get_socio_nombre(self, obj):
        try:
            # Navegación defensiva
            if obj.medidor and obj.medidor.terreno and obj.medidor.terreno.socio:
                return f"{obj.medidor.terreno.socio.nombres} {obj.medidor.terreno.socio.apellidos}"
            return "Sin Socio"
        except Exception:
            return "Error Datos"