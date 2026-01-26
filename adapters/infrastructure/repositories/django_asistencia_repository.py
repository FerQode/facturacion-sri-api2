from typing import Optional, List
from core.domain.asistencia import Asistencia, EstadoJustificacion
from core.interfaces.repositories import IAsistenciaRepository
from adapters.infrastructure.models.evento_models import AsistenciaModel

class DjangoAsistenciaRepository(IAsistenciaRepository):
    def _to_domain(self, model: AsistenciaModel) -> Asistencia:
        return Asistencia(
            id=model.id,
            evento_id=model.evento_id,
            socio_id=model.socio_id,
            asistio=model.asistio,
            estado_justificacion=EstadoJustificacion(model.estado_justificacion),
            multa_factura_id=model.multa_factura_id,
            observacion=model.observacion,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def get_by_id(self, asistencia_id: int) -> Optional[Asistencia]:
        try:
            model = AsistenciaModel.objects.get(id=asistencia_id)
            return self._to_domain(model)
        except AsistenciaModel.DoesNotExist:
            return None

    def get_by_evento(self, evento_id: int) -> List[Asistencia]:
        models = AsistenciaModel.objects.filter(evento_id=evento_id)
        return [self._to_domain(m) for m in models]

    def crear_masivo(self, asistencias: List[Asistencia]) -> List[Asistencia]:
        models_to_create = []
        for asistencia in asistencias:
            models_to_create.append(AsistenciaModel(
                evento_id=asistencia.evento_id,
                socio_id=asistencia.socio_id,
                asistio=asistencia.asistio,
                estado_justificacion=asistencia.estado_justificacion.value,
                observacion=asistencia.observacion
            ))
        
        created_models = AsistenciaModel.objects.bulk_create(models_to_create)
        # Nota: bulk_create no retorna IDs en algunas DBs antiguas, pero en Postgres/modernas sí si se configura.
        # Django retorna instancias, pero podrían no tener ID.
        # Para ser seguros, retornamos lo que Django nos dé, o recargamos si es crítico (aquí no lo es tanto).
        return [self._to_domain(m) for m in created_models]

    def save(self, asistencia: Asistencia) -> Asistencia:
        if asistencia.id:
            model = AsistenciaModel.objects.get(id=asistencia.id)
            model.asistio = asistencia.asistio
            model.estado_justificacion = asistencia.estado_justificacion.value
            model.multa_factura_id = asistencia.multa_factura_id
            model.observacion = asistencia.observacion
        else:
            model = AsistenciaModel(
                evento_id=asistencia.evento_id,
                socio_id=asistencia.socio_id,
                asistio=asistencia.asistio,
                estado_justificacion=asistencia.estado_justificacion.value
            )
        model.save()
        return self._to_domain(model)
