# adapters/api/serializers/medidor_serializers.py
from rest_framework import serializers

class MedidorSerializer(serializers.Serializer):
    """
    Serializer de SALIDA. Se usa para enviar datos al frontend.
    Transforma la Entidad de Dominio 'Medidor' a JSON.
    """
    id = serializers.IntegerField(read_only=True)
    codigo = serializers.CharField(max_length=50)
    socio_id = serializers.IntegerField()
    esta_activo = serializers.BooleanField()
    observacion = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    tiene_medidor_fisico = serializers.BooleanField()

class CrearMedidorSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para crear un medidor.
    Validamos tipos de datos básicos. 
    Nota: La validación de negocio (ej: si el socio existe o el código es único)
    se delega al Caso de Uso (Core), no aquí.
    """
    codigo = serializers.CharField(max_length=50, required=True)
    socio_id = serializers.IntegerField(required=True)
    observacion = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    # Por defecto, asumimos que sí tiene medidor físico si no nos dicen lo contrario
    tiene_medidor_fisico = serializers.BooleanField(default=True)

class ActualizarMedidorSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para actualizar.
    Todos los campos son opcionales (required=False) para permitir 
    actualizaciones parciales (PATCH).
    """
    codigo = serializers.CharField(max_length=50, required=False)
    socio_id = serializers.IntegerField(required=False)
    esta_activo = serializers.BooleanField(required=False)
    observacion = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    tiene_medidor_fisico = serializers.BooleanField(required=False)