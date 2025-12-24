from typing import List, Optional
from core.interfaces.repositories import ISocioRepository
from core.domain.socio import Socio
from adapters.infrastructure.models.socio_model import SocioModel
from core.shared.enums import RolUsuario

class DjangoSocioRepository(ISocioRepository):
    """
    Implementación del Repositorio de Socios usando el ORM de Django.
    Actualizado para manejar barrio_id (FK) y direccion.
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
            
            # --- ACTUALIZACIÓN CRÍTICA ---
            # Mapeamos la Foreign Key correctamente
            barrio_id=model.barrio_id if model.barrio_id else None,
            direccion=model.direccion, 
            # -----------------------------
            
            # Convertimos el string de la BD al Enum del Dominio
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
        try:
            model = SocioModel.objects.select_related('usuario').get(usuario_id=usuario_id)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
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
        """
        Guarda (Create) o Actualiza (Update) un socio en la base de datos.
        """
        if socio.id:
            try:
                # Intentamos obtener el existente
                model = SocioModel.objects.get(pk=socio.id)
            except SocioModel.DoesNotExist:
                # Si viene con ID pero no existe, creamos uno nuevo
                model = SocioModel()
        else:
            # Si no tiene ID, es nuevo
            model = SocioModel()

        # Mapeamos datos de la Entidad -> Modelo de Django
        model.cedula = socio.cedula
        model.nombres = socio.nombres
        model.apellidos = socio.apellidos
        model.email = socio.email
        model.telefono = socio.telefono
        
        # --- MAPEO DE NUEVOS CAMPOS ---
        model.barrio_id = socio.barrio_id  # Django asigna la FK por el ID
        model.direccion = socio.direccion
        # ------------------------------
        
        model.esta_activo = socio.esta_activo
        
        if socio.rol:
            model.rol = socio.rol.value # Guardamos el valor string del Enum
            
        if socio.usuario_id:
            model.usuario_id = socio.usuario_id

        # Guardamos en BD
        model.save()
        
        # Retornamos la entidad actualizada (con el ID generado si era nuevo)
        return self._to_entity(model)