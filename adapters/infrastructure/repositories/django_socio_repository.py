# adapters/infrastructure/repositories/django_socio_repository.py

from typing import List, Optional

# El Contrato (Interfaz) que vamos a implementar
from core.interfaces.repositories import ISocioRepository
# La Entidad (Clase pura de Python) que el "cerebro" entiende
from core.domain.socio import Socio
# El Modelo (Clase de Django) que habla con la BBDD
from adapters.infrastructure.models import SocioModel
# El Enum que necesitamos (recuerda la ruta corregida)
from core.shared.enums import RolUsuario

class DjangoSocioRepository(ISocioRepository):
    """
    Implementación del Repositorio de Socios usando el ORM de Django.
    Este es el "traductor" entre la lógica de Socios y la BBDD.
    """

    def _to_entity(self, model: SocioModel) -> Socio:
        """Mapeador privado: Convierte un Modelo de Django a una Entidad de Dominio."""
        return Socio(
            id=model.id,
            cedula=model.cedula,
            nombres=model.nombres,
            apellidos=model.apellidos,
            email=model.email,
            telefono=model.telefono,
            barrio=model.barrio,
            rol=RolUsuario(model.rol), # Convertimos el string de la BBDD a un Enum
            esta_activo=model.esta_activo
            # 'medidores_ids' se puede cargar aquí si un Caso de Uso lo necesita
        )

    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        """Implementa el método del contrato: Busca un socio por su ID."""
        try:
            model = SocioModel.objects.get(pk=socio_id)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None

    def get_by_cedula(self, cedula: str) -> Optional[Socio]:
        """Implementa el método del contrato: Busca un socio por su cédula."""
        try:
            model = SocioModel.objects.get(cedula=cedula)
            return self._to_entity(model)
        except SocioModel.DoesNotExist:
            return None

    def list_all(self) -> List[Socio]:
        """Implementa el método del contrato: Lista todos los socios."""
        models = SocioModel.objects.all()
        return [self._to_entity(model) for model in models]

    def save(self, socio: Socio) -> Socio:
        """Implementa el método del contrato: Guarda o actualiza un socio."""
        if socio.id:
            # Actualizar un socio existente
            model = SocioModel.objects.get(pk=socio.id)
            model.nombres = socio.nombres
            model.apellidos = socio.apellidos
            model.email = socio.email
            model.telefono = socio.telefono
            model.barrio = socio.barrio
            model.rol = socio.rol.value
            model.esta_activo = socio.esta_activo
        else:
            # Crear un nuevo socio
            model = SocioModel(
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
        socio.id = model.id # Devolvemos el ID a la entidad
        return socio