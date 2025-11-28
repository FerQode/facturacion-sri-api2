# adapters/infrastructure/repositories/django_auth_repository.py
from django.contrib.auth.models import User
from core.interfaces.repositories import IAuthRepository
from core.shared.enums import RolUsuario # <-- Importante: Importar el Enum

class DjangoAuthRepository(IAuthRepository):
    """
    Implementación del repositorio de autenticación usando el modelo User de Django.
    """
    
    def crear_usuario(self, username: str, password: str, email: str = None, rol: RolUsuario = None) -> int:
        """
        Crea un usuario en el sistema de autenticación de Django.
        Si el rol es 'Administrador' o 'Tesorero', le da permisos de staff para entrar al Admin.
        """
        # 1. Validar si el usuario ya existe para evitar errores de integridad
        if User.objects.filter(username=username).exists():
            raise ValueError(f"El nombre de usuario '{username}' ya existe.")

        # 2. Crear el usuario usando el helper de Django (hashea la contraseña automáticamente)
        user = User.objects.create_user(username=username, password=password, email=email)
        
        # 3. Lógica de permisos basada en Rol (RBAC simple)
        # Solo damos acceso al panel de administración (is_staff) a roles específicos
        if rol in [RolUsuario.ADMINISTRADOR, RolUsuario.TESORERO]:
            user.is_staff = True
            user.save()
            
        return user.id

    def desactivar_usuario(self, user_id: int) -> None:
        """ 
        Desactiva un usuario para que no pueda loguearse.
        Esto se usa cuando eliminamos (soft delete) un Socio.
        """
        try:
            user = User.objects.get(pk=user_id)
            user.is_active = False
            user.save()
        except User.DoesNotExist:
            pass # Si no existe, no hacemos nada (idempotencia)