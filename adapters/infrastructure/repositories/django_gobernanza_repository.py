# adapters/infrastructure/repositories/django_gobernanza_repository.py
from typing import List, Any
from core.interfaces.repositories import IGobernanzaRepository
from core.domain.asistencia import EstadoAsistencia
from adapters.infrastructure.models import AsistenciaModel

class DjangoGobernanzaRepository(IGobernanzaRepository):
    
    def obtener_multas_pendientes(self, socio_id: int) -> List[Any]:
        # Busca asistencias con estado FALTA y sin factura asociada
        return list(AsistenciaModel.objects.filter(
            socio_id=socio_id,
            estado=EstadoAsistencia.FALTA.value,
            multa_factura__isnull=True
        ).select_related('evento'))

    def marcar_multa_como_facturada(self, asistencia_id: int, factura_id: int) -> None:
        AsistenciaModel.objects.filter(id=asistencia_id).update(multa_factura_id=factura_id)
