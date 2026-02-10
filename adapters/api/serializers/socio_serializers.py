# adapters/api/serializers/socio_serializers.py
from rest_framework import serializers
from core.shared.enums import RolUsuario

class SocioSerializer(serializers.Serializer):
    """
    Serializer de SALIDA (Lectura).
    Muestra los datos del Socio tal como vienen del DTO.
    """
    id = serializers.IntegerField(read_only=True)
    identificacion = serializers.CharField(max_length=13)
    tipo_identificacion = serializers.CharField(max_length=1)
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    
    # --- CAMBIOS DE SINCRONIZACIÓN ---
    # POR ESTA LÍNEA (Usamos source para mantener el nombre 'barrio' en el JSON):
    barrio = serializers.IntegerField(source='barrio_id', allow_null=True)
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
    identificacion = serializers.CharField(max_length=13)
    tipo_identificacion = serializers.ChoiceField(choices=['C', 'R', 'P'], default='C')
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

    def validate(self, data):
        """ 
        Validación cruzada y algorítmica usando el Dominio Puro 
        """
        # 1. Validación de Formato (Longitud vs Tipo)
        tipo = data.get('tipo_identificacion')
        identificacion = data.get('identificacion', '')
        
        # Importamos el modelo solo para acceder a las constantes de choices si es necesario,
        # o usamos literales 'C', 'R', 'P' que coinciden con el ChoiceField.
        
        if tipo == 'C':
            if len(identificacion) != 10:
                raise serializers.ValidationError({
                    "identificacion": "La Cédula requiere exactamente 10 dígitos. Si es RUC, cambie el tipo a 'R'."
                })
        elif tipo == 'R':
            if len(identificacion) != 13:
                raise serializers.ValidationError({
                    "identificacion": "El RUC requiere exactamente 13 dígitos."
                })
        elif tipo == 'P':
            if len(identificacion) < 5:
                raise serializers.ValidationError({
                    "identificacion": "El Pasaporte debe tener al menos 5 caracteres."
                })

        # 2. Validación de Algoritmo (Dominio)
        from core.domain.socio import Socio
        
        # Validamos usando la entidad de dominio (DRY - Don't Repeat Yourself)
        try:
            # Creamos una instancia "dummy" solo para validar
            # Nota: Al no pasar _validate, usa el default True (que es lo que queremos)
            Socio(
                id=None,
                identificacion=identificacion,
                tipo_identificacion=tipo,
                nombres=data.get('nombres'),
                apellidos=data.get('apellidos')
            )
        except ValueError as e:
            raise serializers.ValidationError({"identificacion": str(e)})

        return data

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