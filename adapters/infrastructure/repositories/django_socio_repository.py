# adapters/infrastructure/repositories/django_socio_repository.py

from typing import List, Optional
from core.interfaces.repositories import ISocioRepository
from core.domain.socio import Socio
from adapters.infrastructure.models import SocioModel
from core.shared.enums import RolUsuario


class DjangoSocioRepository(ISocioRepository):
    """
    Implementación del Repositorio de Socios usando el ORM de Django.
    """

    def _to_entity(self, model: SocioModel) -> Socio:
        """Mapeador: Modelo -> Entidad"""
        return Socio(
            id=model.id,
            # --- MAPEO DEL NUEVO CAMPO ---
            usuario_id=model.usuario.id if model.usuario else None,
            # -----------------------------
            cedula=model.cedula,
            nombres=model.nombres,
            apellidos=model.apellidos,
            email=model.email,
            telefono=model.telefono,
            barrio=model.barrio,
            rol=RolUsuario(model.rol),
            esta_activo=model.esta_activo
        )

    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        try:
            # Usamos select_related para traer el usuario en la misma consulta
            model = SocioModel.objects.select_related('usuario').get(pk=socio_id)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None

    # =======================================================
    # MÉTODO CLAVE QUE FALTABA (SOLUCIÓN AL PROBLEMA)
    # =======================================================
    def get_by_usuario_id(self, usuario_id: int) -> Optional[Socio]:
        """Busca un socio por el ID del usuario de Django (auth_user.id)."""
        try:
            # Buscamos por el campo 'usuario_id' (la FK en la BBDD)
            # select_related optimiza la carga
            model = SocioModel.objects.select_related('usuario').get(usuario_id=usuario_id)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None
        except Exception:
            # Si hay un error inesperado, lo capturamos
            return None

    # =======================================================

    def get_by_cedula(self, cedula: str) -> Optional[Socio]:
        try:
            model = SocioModel.objects.get(cedula=cedula)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None

    def list_all(self) -> List[Socio]:
        # Usamos select_related para evitar consultas N+1 al listar todos
        models = SocioModel.objects.select_related('usuario').all()
        return [self._to_entity(model) for model in models]

    def save(self, socio: Socio) -> Socio:
        """Guarda o actualiza un socio."""
        if socio.id:
            # Update
            try:
                model = SocioModel.objects.get(pk=socio.id)
                model.nombres = socio.nombres
                model.apellidos = socio.apellidos
                model.email = socio.email
                model.telefono = socio.telefono
                model.barrio = socio.barrio
                model.rol = socio.rol.value
                model.esta_activo = socio.esta_activo
                # Si se asigna/cambia el usuario
                if socio.usuario_id:
                    model.usuario_id = socio.usuario_id
            except SocioModel.DoesNotExist:
                # Fallback: crear si no existe (aunque no debería pasar con ID)
                return self.save_new(socio)
        else:
            return self.save_new(socio)

        model.save()
        return self._to_entity(model)

    def save_new(self, socio: Socio) -> Socio:
        """Helper para crear nuevo socio"""
        model = SocioModel(
            # --- GUARDADO DEL NUEVO CAMPO ---
            usuario_id=socio.usuario_id,
            # --------------------------------
            cedula=socio.cedula,
            nombres=socio.nombres,
            apellidos=socio.apellidos,
            email=socio.email,
            telefono=socio.telefono,
            barrio=socio.barrio,
            rol=socio.rol.value,
            esta_activo=socio.esta_activo
        )
        model.save()
        socio.id = model.id
        return socio