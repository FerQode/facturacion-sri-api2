# adapters/api/serializers/medidor_serializers.py

from rest_framework import serializers

class MedidorSerializer(serializers.Serializer):
    """
    Serializer de SALIDA (Output).
    Transforma la Entidad/DTO 'Medidor' a JSON para responder al cliente.
    """
    id = serializers.IntegerField(read_only=True)
    # Ahora vinculamos al Terreno, no al Socio
    terreno_id = serializers.IntegerField(allow_null=True, help_text="ID del terreno donde está instalado")
    
    codigo = serializers.CharField()
    marca = serializers.CharField(allow_null=True)
    
    # Lectura inicial es vital para cálculos (Float para compatibilidad JSON)
    lectura_inicial = serializers.FloatField()
    
    # 'estado' reemplaza a 'esta_activo'. Ej: ACTIVO, DANADO, ROBADO.
    estado = serializers.CharField()
    
    observacion = serializers.CharField(allow_null=True)
    fecha_instalacion = serializers.CharField(allow_null=True, read_only=True)


class RegistrarMedidorSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA (Input) para crear un medidor.
    Validamos formato antes de pasar al Caso de Uso.
    """
    terreno_id = serializers.IntegerField(required=True, help_text="Terreno donde se instalará")
    codigo = serializers.CharField(max_length=50, required=True)
    marca = serializers.CharField(max_length=50, required=False, allow_blank=True)
    lectura_inicial = serializers.FloatField(required=False, default=0.0)
    observacion = serializers.CharField(required=False, allow_blank=True)

    # Nota: No pedimos 'estado' ni 'fecha_instalacion', eso lo define el sistema al crear.


class ActualizarMedidorSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para correcciones (PATCH).
    Solo permite editar datos descriptivos, NO estructurales.
    """
    codigo = serializers.CharField(max_length=50, required=False)
    marca = serializers.CharField(max_length=50, required=False)
    observacion = serializers.CharField(required=False, allow_blank=True)
    
    # IMPORTANTE:
    # No permitimos actualizar 'terreno_id', 'estado' o 'lectura_inicial' aquí.
    # Esos cambios requieren procesos de negocio (Reemplazo, Traslado, etc).