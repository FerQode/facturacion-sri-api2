# adapters/api/serializers/socio_serializers.py
from rest_framework import serializers
from core.shared.enums import RolUsuario

class SocioSerializer(serializers.Serializer):
    """
    Traduce entre JSON y los DTOs de Socio.
    Maneja la validación de entrada y el formato de salida.
    """
    # Campos de Salida (leídos desde el SocioDTO)
    id = serializers.IntegerField(read_only=True)
    cedula = serializers.CharField(max_length=10)
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    barrio = serializers.CharField(max_length=100)
    rol = serializers.ChoiceField(choices=[rol.value for rol in RolUsuario])
    email = serializers.EmailField(allow_blank=True, required=False)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    esta_activo = serializers.BooleanField()

    # Este serializer no se usará para 'update' (PUT/PATCH),
    # ya que la lógica de "parcheo" está en el Caso de Uso.
    # Crearemos uno separado para 'update' si es necesario.

class CrearSocioSerializer(serializers.Serializer):
    """ Serializer específico para crear un Socio """
    cedula = serializers.CharField(max_length=10)
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    barrio = serializers.CharField(max_length=100)
    rol = serializers.ChoiceField(choices=[rol.value for rol in RolUsuario])
    email = serializers.EmailField(allow_blank=True, required=False)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    
    def validate_rol(self, value):
        """ Convierte el string (ej: "Socio") de vuelta a un Enum """
        return RolUsuario(value)

class ActualizarSocioSerializer(serializers.Serializer):
    """ Serializer para actualizar (PATCH). Todos los campos opcionales. """
    nombres = serializers.CharField(max_length=100, required=False)
    apellidos = serializers.CharField(max_length=100, required=False)
    barrio = serializers.CharField(max_length=100, required=False)
    rol = serializers.ChoiceField(choices=[rol.value for rol in RolUsuario], required=False)
    email = serializers.EmailField(allow_blank=True, required=False)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    esta_activo = serializers.BooleanField(required=False)
    
    def validate_rol(self, value):
        """ Convierte el string (ej: "Socio") de vuelta a un Enum """
        return RolUsuario(value)