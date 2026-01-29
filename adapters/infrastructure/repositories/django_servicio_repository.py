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

    def get_by_socio(self, socio_id: int) -> List[Any]:
        qs = ServicioModel.objects.filter(socio_id=socio_id)
        # Return simpler dicts/objects for DTO mapping
        return list(qs.values('id', 'terreno_id', 'tipo'))

    def get_active_by_terreno_and_type(self, terreno_id: int, tipo: str) -> Any:
        return ServicioModel.objects.filter(
            terreno_id=terreno_id,
            tipo=tipo,
            activo=True
        ).first()