# adapters/infrastructure/repositories/django_socio_repository.py

from typing import List, Optional
from core.interfaces.repositories import ISocioRepository
from core.domain.socio import Socio
from adapters.infrastructure.models.socio_model import SocioModel
from core.shared.enums import RolUsuario


class DjangoSocioRepository(ISocioRepository):
    """
    Implementación del Repositorio de Socios usando el ORM de Django.
    CORREGIDO: Ajustado a los cambios de base de datos (barrio_domicilio).
    """

    def _to_entity(self, model: SocioModel) -> Socio:
        """Mapeador: Modelo de Django -> Entidad de Dominio"""
        return Socio(
            id=model.id,
            usuario_id=model.usuario.id if model.usuario else None,
            cedula=model.cedula,
            nombres=model.nombres,
            apellidos=model.apellidos,
            email=model.email,
            telefono=model.telefono,
            
            # --- CORRECCIÓN 1: Usamos los campos nuevos ---
            # Antes: barrio=model.barrio
            # Ahora: Mapeamos al ID del barrio domicilio y agregamos dirección
            barrio_id=model.barrio_domicilio_id if model.barrio_domicilio_id else None,
            direccion=model.direccion, 
            # ---------------------------------------------
            
            # Nota: Si tu entidad Socio usa 'rol' como Enum, lo convertimos:
            rol=RolUsuario(model.rol) if model.rol else None,
            esta_activo=model.esta_activo
        )

    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        try:
            model = SocioModel.objects.select_related('usuario').get(pk=socio_id)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None

    def get_by_usuario_id(self, usuario_id: int) -> Optional[Socio]:
        """Busca un socio por el ID del usuario de Django."""
        try:
            model = SocioModel.objects.select_related('usuario').get(usuario_id=usuario_id)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None
        except Exception:
            return None

    def get_by_cedula(self, cedula: str) -> Optional[Socio]:
        try:
            model = SocioModel.objects.get(cedula=cedula)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None

    def list_all(self) -> List[Socio]:
        models = SocioModel.objects.select_related('usuario').all()
        return [self._to_entity(model) for model in models]

    def save(self, socio: Socio) -> Socio:
        """Guarda o actualiza un socio."""
        if socio.id:
            # Update
            try:
                model = SocioModel.objects.get(pk=socio.id)
                self._map_entity_to_model(socio, model) # Usamos helper para no repetir código
            except SocioModel.DoesNotExist:
                return self.save_new(socio)
        else:
            return self.save_new(socio)

        model.save()
        socio.id = model.id # Aseguramos que el ID persista en la entidad
        return self._to_entity(model)

    def save_new(self, socio: Socio) -> Socio:
        """Helper para crear nuevo socio"""
        model = SocioModel()
        self._map_entity_to_model(socio, model)
        model.save()
        socio.id = model.id
        return socio

    def _map_entity_to_model(self, socio: Socio, model: SocioModel):
        """
        Helper privado para pasar datos de Entidad -> Modelo.
        Evita duplicar código en save() y save_new().
        """
        model.usuario_id = socio.usuario_id
        model.cedula = socio.cedula
        model.nombres = socio.nombres
        model.apellidos = socio.apellidos
        model.email = socio.email
        model.telefono = socio.telefono
        
        # --- CORRECCIÓN 2: Guardado en campos correctos ---
        # El modelo espera 'barrio_domicilio_id', no 'barrio'
        model.barrio_domicilio_id = socio.barrio_id 
        model.direccion = socio.direccion
        # --------------------------------------------------
        
        if socio.rol:
            model.rol = socio.rol.value
        model.esta_activo = socio.esta_activo