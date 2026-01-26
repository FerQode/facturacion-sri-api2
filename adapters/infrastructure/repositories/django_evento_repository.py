from typing import Optional, List
from core.domain.evento import Evento, TipoEvento, EstadoEvento
from core.interfaces.repositories import IEventoRepository
from adapters.infrastructure.models.evento_models import EventoModel

class DjangoEventoRepository(IEventoRepository):
    def _to_domain(self, model: EventoModel) -> Evento:
        return Evento(
            id=model.id,
            nombre=model.nombre,
            tipo=TipoEvento(model.tipo),
            fecha=model.fecha,
            valor_multa=float(model.valor_multa),
            estado=EstadoEvento(model.estado),
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def get_by_id(self, evento_id: int) -> Optional[Evento]:
        try:
            model = EventoModel.objects.get(id=evento_id)
            return self._to_domain(model)
        except EventoModel.DoesNotExist:
            return None

    def save(self, evento: Evento) -> Evento:
        if evento.id:
            model = EventoModel.objects.get(id=evento.id)
            model.nombre = evento.nombre
            model.tipo = evento.tipo.value
            model.fecha = evento.fecha
            model.valor_multa = evento.valor_multa
            model.estado = evento.estado.value
        else:
            model = EventoModel(
                nombre=evento.nombre,
                tipo=evento.tipo.value,
                fecha=evento.fecha,
                valor_multa=evento.valor_multa,
                estado=evento.estado.value
            )
        model.save()
        return self._to_domain(model)

    def list_all(self) -> List[Evento]:
        models = EventoModel.objects.all().order_by('-fecha')
        return [self._to_domain(m) for m in models]
