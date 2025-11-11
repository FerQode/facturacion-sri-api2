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
    Esta clase CUMPLE el contrato definido en ILecturaRepository.
    """

    def _to_entity(self, model: LecturaModel) -> Lectura:
        """
        Mapeador privado: Convierte un Modelo de Django (datos de la BBDD)
        a una Entidad de Dominio (lógica de negocio pura).
        """
        return Lectura(
            id=model.id,
            medidor_id=model.medidor_id,
            fecha_lectura=model.fecha_lectura,
            lectura_actual_m3=model.lectura_actual_m3,
            lectura_anterior_m3=model.lectura_anterior_m3
        )

    # --- MÉTODO CLAVE QUE FALTABA ---
    def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        """
        Implementación de get_by_id.
        Busca una lectura por su Primary Key (ID).
        Este método es requerido por el GenerarFacturaUseCase.
        """
        try:
            # 1. Usa el ORM de Django para buscar el modelo
            model = LecturaModel.objects.get(pk=lectura_id)
            # 2. Traduce el modelo a una entidad y la devuelve
            return self._to_entity(model)
        except LecturaModel.DoesNotExist:
            # Si Django no lo encuentra, devolvemos None
            return None
    # ---------------------------------

    def get_latest_by_medidor(self, medidor_id: int) -> Optional[Lectura]:
        """
        Obtiene la última lectura registrada para un medidor específico.
        """
        try:
            model = LecturaModel.objects.filter(medidor_id=medidor_id).latest()
            return self._to_entity(model)
        except LecturaModel.DoesNotExist:
            return None

    def save(self, lectura: Lectura) -> Lectura:
        """
        Guarda una nueva entidad Lectura en la base de datos.
        """
        model = LecturaModel(
            medidor_id=lectura.medidor_id,
            fecha_lectura=lectura.fecha_lectura,
            lectura_actual_m3=lectura.lectura_actual_m3,
            lectura_anterior_m3=lectura.lectura_anterior_m3
        )
        model.save()
        
        lectura.id = model.id
        return lectura