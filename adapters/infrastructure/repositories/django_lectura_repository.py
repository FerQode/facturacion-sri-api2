# adapters/infrastructure/repositories/django_lectura_repository.py

from typing import List, Optional

# Contratos (Interfaces)
from core.interfaces.repositories import ILecturaRepository
# Entidades (Dominio)
from core.domain.lectura import Lectura
# Modelos (Base de Datos)
from adapters.infrastructure.models.lectura_model import LecturaModel

class DjangoLecturaRepository(ILecturaRepository):
    """
    Implementación del Repositorio de Lecturas usando el ORM de Django.
    Actualizado para Fase 4 (Soporte de decimales y nuevos campos).
    """

    def _to_entity(self, model: LecturaModel) -> Lectura:
        """
        Mapeador: Modelo Django -> Entidad Dominio.
        """
        return Lectura(
            id=model.id,
            medidor_id=model.medidor_id,
            
            # --- CAMBIOS CRÍTICOS ---
            # 1. Mapeamos 'valor' (Decimal en BDD) a float (Entidad)
            valor=float(model.valor), 
            
            # 2. Mapeamos 'fecha' (antes fecha_lectura)
            fecha=model.fecha,
            
            # 3. Nuevos campos de auditoría
            observacion=model.observacion,
            esta_facturada=model.esta_facturada
            
            # Nota: 'lectura_anterior' es opcional en la entidad y no se guarda 
            # en la fila actual del modelo, por eso no lo asignamos aquí 
            # (se calcula en tiempo de ejecución si se necesita).
        )

    def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        try:
            model = LecturaModel.objects.get(pk=lectura_id)
            return self._to_entity(model)
        except LecturaModel.DoesNotExist:
            return None

    def get_latest_by_medidor(self, medidor_id: int) -> Optional[Lectura]:
        """
        Obtiene la última lectura registrada para un medidor.
        Vital para calcular el consumo del siguiente mes.
        """
        try:
            # Usamos 'latest()' basado en el 'get_latest_by' definido en el Meta del modelo
            model = LecturaModel.objects.filter(medidor_id=medidor_id).latest()
            return self._to_entity(model)
        except LecturaModel.DoesNotExist:
            return None

    def list_by_medidor_id(self, medidor_id: int) -> List[Lectura]:
        """
        Devuelve el historial de lecturas de un medidor.
        """
        models = LecturaModel.objects.filter(medidor_id=medidor_id).order_by('-fecha')
        return [self._to_entity(m) for m in models]

    def save(self, lectura: Lectura) -> Lectura:
        """
        Guarda o actualiza una lectura.
        """
        if lectura.id:
            # Update
            try:
                model = LecturaModel.objects.get(pk=lectura.id)
            except LecturaModel.DoesNotExist:
                model = LecturaModel()
        else:
            # Create
            model = LecturaModel()

        # Mapeo Entidad -> Modelo
        model.medidor_id = lectura.medidor_id
        
        # --- CAMBIOS CRÍTICOS ---
        model.valor = lectura.valor  # Guardamos en el campo nuevo
        model.fecha = lectura.fecha
        model.observacion = lectura.observacion
        model.esta_facturada = lectura.esta_facturada
        
        model.save()
        
        # Devolvemos la entidad con el ID generado
        return self._to_entity(model)