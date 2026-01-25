from typing import List, Any
from core.interfaces.repositories import IServicioRepository
from adapters.infrastructure.models.servicio_model import ServicioModel

class DjangoServicioRepository(IServicioRepository):
    def obtener_servicios_fijos_activos(self) -> List[Any]:
        # Retorna queryset de Django (que cumple con ser iterable)
        # Select related para optimizar acceso a socio y terreno (usado luego en el UseCase)
        return ServicioModel.objects.filter(
            tipo='FIJO',
            activo=True
        ).select_related('socio', 'terreno')

    def create_automatico(self, terreno_id: int, socio_id: int, tipo: str, valor: float) -> Any:
        return ServicioModel.objects.create(
            terreno_id=terreno_id,
            socio_id=socio_id,
            tipo=tipo,
            valor_tarifa=valor,
            activo=True
        )