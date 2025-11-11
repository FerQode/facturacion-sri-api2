# adapters/infrastructure/repositories/django_medidor_repository.py

from typing import List, Optional

# Contratos (Interfaces) que vamos a implementar
from core.interfaces.repositories import IMedidorRepository
# Entidades (Clases puras)
from core.domain.medidor import Medidor
# Modelos (Clases de Django)
from adapters.infrastructure.models import MedidorModel

class DjangoMedidorRepository(IMedidorRepository):
    """
    Implementación del Repositorio de Medidores usando el ORM de Django.
    """

    def _to_entity(self, model: MedidorModel) -> Medidor:
        """Mapeador: Convierte un Modelo de Django a una Entidad de Dominio."""
        return Medidor(
            id=model.id,
            codigo=model.codigo,
            socio_id=model.socio_id,
            esta_activo=model.esta_activo,
            observacion=model.observacion,
            tiene_medidor_fisico=model.tiene_medidor_fisico
        )

    def get_by_id(self, medidor_id: int) -> Optional[Medidor]:
        try:
            model = MedidorModel.objects.get(pk=medidor_id)
            return self._to_entity(model)
        except MedidorModel.DoesNotExist:
            return None

    def list_by_socio(self, socio_id: int) -> List[Medidor]:
        models = MedidorModel.objects.filter(socio_id=socio_id)
        return [self._to_entity(model) for model in models]

    def save(self, medidor: Medidor) -> Medidor:
        """Guarda o actualiza un medidor."""
        if medidor.id:
            model = MedidorModel.objects.get(pk=medidor.id)
            model.codigo = medidor.codigo
            model.esta_activo = medidor.esta_activo
            model.observacion = medidor.observacion
            model.tiene_medidor_fisico = medidor.tiene_medidor_fisico
        else:
            model = MedidorModel(
                socio_id=medidor.socio_id,
                codigo=medidor.codigo,
                esta_activo=medidor.esta_activo,
                observacion=medidor.observacion,
                tiene_medidor_fisico=medidor.tiene_medidor_fisico
            )
        
        model.save()
        return self._to_entity(model)