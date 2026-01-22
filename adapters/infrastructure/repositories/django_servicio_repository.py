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