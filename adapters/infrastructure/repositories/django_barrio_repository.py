# adapters/infrastructure/repositories/django_barrio_repository.py

from typing import List, Optional
from core.interfaces.repositories import IBarrioRepository
from core.domain.barrio import Barrio
from adapters.infrastructure.models import BarrioModel

class DjangoBarrioRepository(IBarrioRepository):
    """
    Implementación del Repositorio de Barrios usando el ORM de Django.
    """

    def _to_entity(self, model: BarrioModel) -> Barrio:
        """Helper para convertir Modelo Django -> Entidad Dominio"""
        return Barrio(
            id=model.id,
            nombre=model.nombre,
            descripcion=model.descripcion,
            activo=model.activo
        )

    def list_all(self) -> List[Barrio]:
        """Devuelve todos los barrios (solo los activos por defecto, o todos?)"""
        # Por regla general, listamos solo los activos para los selects
        models = BarrioModel.objects.all().order_by('id')
        return [self._to_entity(m) for m in models]

    def get_by_id(self, barrio_id: int) -> Optional[Barrio]:
        try:
            model = BarrioModel.objects.get(pk=barrio_id)
            return self._to_entity(model)
        except BarrioModel.DoesNotExist:
            return None
    
    def get_by_nombre(self, nombre: str) -> Optional[Barrio]:
        """Búsqueda insensible a mayúsculas/minúsculas para evitar duplicados"""
        try:
            model = BarrioModel.objects.get(nombre__iexact=nombre)
            return self._to_entity(model)
        except BarrioModel.DoesNotExist:
            return None

    def save(self, barrio: Barrio) -> Barrio:
        if barrio.id:
            # Update
            model = BarrioModel.objects.get(pk=barrio.id)
            model.nombre = barrio.nombre
            model.descripcion = barrio.descripcion
            model.activo = barrio.activo
        else:
            # Create
            model = BarrioModel(
                nombre=barrio.nombre,
                descripcion=barrio.descripcion,
                activo=barrio.activo
            )
        
        model.save()
        barrio.id = model.id
        return barrio
    
    def delete(self, barrio_id: int) -> None:
        """Soft delete (desactivación)"""
        try:
            model = BarrioModel.objects.get(pk=barrio_id)
            model.activo = False
            model.save()
        except BarrioModel.DoesNotExist:
            pass