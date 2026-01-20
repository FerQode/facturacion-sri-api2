# adapters/infrastructure/repositories/django_servicio_repository.py

from core.interfaces.repositories import IServicioRepository
from adapters.infrastructure.models import ServicioModel

class DjangoServicioRepository(IServicioRepository):
    """
    Implementación en Django para la gestión automática de servicios de agua.
    """
    def create_automatico(self, terreno_id: int, socio_id: int, tipo: str, valor: float):
        """
        Inserta el registro en la tabla servicios_agua de MySQL.
        """
        return ServicioModel.objects.create(
            terreno_id=terreno_id,
            socio_id=socio_id,
            tipo=tipo,
            valor_tarifa=valor,
            activo=True
        )