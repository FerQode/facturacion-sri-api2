from rest_framework import serializers
from adapters.infrastructure.models import LecturaModel

class RegistrarLecturaSerializer(serializers.Serializer):
    """
    Valida el JSON de ENTRADA para registrar una lectura.
    """
    medidor_id = serializers.IntegerField(required=True)
    lectura_actual_m3 = serializers.DecimalField(required=True, min_value=0, max_digits=12, decimal_places=2)
    fecha_lectura = serializers.DateField(required=True)
    operador_id = serializers.IntegerField(required=True)

class LecturaResponseSerializer(serializers.ModelSerializer):
    """
    Serializador de SALIDA.
    Adapta la Entidad de Dominio (Python puro) al formato JSON esperado.
    """
    
    # --- CORRECCIÓN 1: Mapeo de ID ---
    # La entidad tiene 'medidor_id', declaramos el campo explícitamente como entero.
    medidor_id = serializers.IntegerField()

    # --- CORRECCIÓN 2: Mapeo de Nombres ---
    # En la Entidad se llama 'consumo_del_mes_m3', pero en el JSON queremos 'consumo_del_mes'.
    # Usamos source='...' para hacer el puente.
    consumo_del_mes = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True, 
        source='consumo_del_mes_m3' # <--- Aquí está la magia
    )

    lectura_anterior = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = LecturaModel
        fields = [
            'id',
            'medidor_id',       # <--- CAMBIADO: Antes decía 'medidor'
            'fecha',
            'valor',            
            'lectura_anterior', 
            'consumo_del_mes',  
            'observacion',
            'esta_facturada'
        ]