# adapters/api/serializers/socio_serializers.py
from rest_framework import serializers
from core.shared.enums import RolUsuario

class SocioSerializer(serializers.Serializer):
    """
    Serializer de SALIDA (Lectura).
    Muestra los datos del Socio tal como vienen del DTO.
    """
    id = serializers.IntegerField(read_only=True)
    cedula = serializers.CharField(max_length=10)
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    
    # --- CAMBIOS DE SINCRONIZACIÓN ---
    # Antes: barrio = serializers.CharField(...)
    barrio_id = serializers.IntegerField(allow_null=True) # ID numérico del barrio
    direccion = serializers.CharField(max_length=200, allow_null=True, required=False) # Nueva dirección
    # ---------------------------------

    rol = serializers.ChoiceField(choices=[rol.value for rol in RolUsuario])
    email = serializers.EmailField(allow_blank=True, required=False)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    esta_activo = serializers.BooleanField()

class CrearSocioSerializer(serializers.Serializer):
    """ 
    Serializer de ENTRADA (Creación).
    Valida que los datos sean correctos antes de pasar al Caso de Uso.
    """
    cedula = serializers.CharField(max_length=10)
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    
    # --- CAMBIOS DE SINCRONIZACIÓN ---
    # El Frontend debe enviar el ID del barrio seleccionado en el dropdown
    barrio_id = serializers.IntegerField() 
    direccion = serializers.CharField(max_length=200) # Obligatorio al crear
    # ---------------------------------

    rol = serializers.ChoiceField(choices=[rol.value for rol in RolUsuario])
    email = serializers.EmailField(allow_blank=True, required=False)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    
    # Campos opcionales de autenticación
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    
    def validate_rol(self, value):
        """ Convierte el string (ej: "Socio") de vuelta a un Enum """
        return RolUsuario(value)

class ActualizarSocioSerializer(serializers.Serializer):
    """ 
    Serializer de ENTRADA (Actualización Parcial - PATCH). 
    Todos los campos son opcionales.
    """
    nombres = serializers.CharField(max_length=100, required=False)
    apellidos = serializers.CharField(max_length=100, required=False)
    
    # --- CAMBIOS DE SINCRONIZACIÓN ---
    barrio_id = serializers.IntegerField(required=False)
    direccion = serializers.CharField(max_length=200, required=False)
    # ---------------------------------

    rol = serializers.ChoiceField(choices=[rol.value for rol in RolUsuario], required=False)
    email = serializers.EmailField(allow_blank=True, required=False)
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    esta_activo = serializers.BooleanField(required=False)
    
    def validate_rol(self, value):
        return RolUsuario(value)