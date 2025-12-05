# adapters/api/serializers/auth_serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.shared.enums import RolUsuario

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el token JWT para incluir información extra del usuario (Claims).
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 1. Añadir el nombre de usuario
        token['username'] = user.username
        
        # 2. Añadir el Rol
        # Buscamos si el usuario tiene un perfil de Socio asociado
        if hasattr(user, 'perfil_socio'):
            # Si es un Socio, obtenemos su rol desde la entidad Socio
            # (Guardamos el valor string del enum, ej: "Tesorero")
            token['rol'] = user.perfil_socio.rol 
            token['socio_id'] = user.perfil_socio.id
        elif user.is_superuser:
            # Si es superuser y no tiene socio, le ponemos rol Admin
            token['rol'] = RolUsuario.ADMINISTRADOR.value
            token['socio_id'] = None
        else:
            # Caso fallback
            token['rol'] = "Usuario"
            token['socio_id'] = None

        return token