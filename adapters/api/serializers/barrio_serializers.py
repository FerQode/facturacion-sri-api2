# adapters/api/serializers/barrio_serializers.py
from rest_framework import serializers

class BarrioSerializer(serializers.Serializer):
    """
    Serializer de SALIDA.
    Transforma la Entidad de Dominio 'Barrio' a JSON para enviarlo al frontend.
    """
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(max_length=150)
    descripcion = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    activo = serializers.BooleanField()

class CrearBarrioSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para crear un barrio.
    Validamos tipos de datos básicos.
    """
    nombre = serializers.CharField(max_length=150, required=True)
    descripcion = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    activo = serializers.BooleanField(default=True)

class ActualizarBarrioSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para actualizar.
    Todos los campos son opcionales para permitir actualizaciones parciales (PATCH).
    """
    nombre = serializers.CharField(max_length=150, required=False)
    descripcion = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    activo = serializers.BooleanField(required=False)