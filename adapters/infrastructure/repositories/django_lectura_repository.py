# adapters/infrastructure/repositories/django_lectura_repository.py

from typing import Optional

# Contratos (Interfaces) que vamos a implementar
from core.interfaces.repositories import ILecturaRepository
# Entidades (Clases puras) que el Caso de Uso espera recibir
from core.domain.lectura import Lectura
# Modelos (Clases de Django) que usaremos para la BBDD
from adapters.infrastructure.models import LecturaModel

class DjangoLecturaRepository(ILecturaRepository):
    """
    Implementación del Repositorio de Lecturas usando el ORM de Django.
    """

    def _to_entity(self, model: LecturaModel) -> Lectura:
        """Mapeador: Convierte un Modelo de Django a una Entidad de Dominio."""
        return Lectura(
            id=model.id,
            medidor_id=model.medidor_id,
            fecha_lectura=model.fecha_lectura,
            lectura_actual_m3=model.lectura_actual_m3,
            lectura_anterior_m3=model.lectura_anterior_m3
        )

    def get_latest_by_medidor(self, medidor_id: int) -> Optional[Lectura]:
        try:
            # get_latest_by = 'fecha_lectura' (lo definimos en el Modelo)
            model = LecturaModel.objects.filter(medidor_id=medidor_id).latest()
            return self._to_entity(model)
        except LecturaModel.DoesNotExist:
            return None

    def save(self, lectura: Lectura) -> Lectura:
        """Guarda una nueva lectura."""
        model = LecturaModel(
            medidor_id=lectura.medidor_id,
            fecha_lectura=lectura.fecha_lectura,
            lectura_actual_m3=lectura.lectura_actual_m3,
            lectura_anterior_m3=lectura.lectura_anterior_m3
        )
        model.save()
        return self._to_entity(model) # Devolvemos la entidad con el ID