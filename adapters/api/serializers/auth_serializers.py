# adapters/api/serializers/auth_serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.shared.enums import RolUsuario

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el token JWT para incluir información extra del usuario (Claims).
    Adaptado para devolver nombres reales del Socio si existen.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 1. Datos básicos de cuenta
        token['username'] = user.username
        
        # 2. LÓGICA DE FUSIÓN (Auth User + Tabla Socio)
        # Verificamos si el usuario tiene un perfil de Socio asociado
        # 'perfil_socio' es el related_name definido en SocioModel
        if hasattr(user, 'perfil_socio') and user.perfil_socio:
            socio = user.perfil_socio
            
            # --- ¡AQUÍ ESTÁ LA MAGIA PARA EL FRONTEND! ---
            # Sacamos los nombres de la tabla SOCIO, donde están los datos reales
            token['first_name'] = socio.nombres 
            token['last_name'] = socio.apellidos 
            
            token['rol'] = socio.rol 
            token['socio_id'] = socio.id
            
        else:
            # CASO: ADMIN / USUARIO SIN PERFIL DE SOCIO
            # Aquí sí usamos los datos de la tabla de usuarios de Django
            token['first_name'] = user.first_name
            token['last_name'] = user.last_name

            if user.is_superuser:
                token['rol'] = RolUsuario.ADMINISTRADOR.value
            else:
                token['rol'] = "Usuario"
            
            token['socio_id'] = None

        return token