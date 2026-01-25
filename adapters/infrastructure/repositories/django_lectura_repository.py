# adapters/infrastructure/repositories/django_lectura_repository.py

from typing import List, Optional
from core.interfaces.repositories import ILecturaRepository
from core.domain.lectura import Lectura
from adapters.infrastructure.models import LecturaModel

class DjangoLecturaRepository(ILecturaRepository):
    """
    Implementación del Repositorio de Lecturas usando Django ORM.
    Cumple estrictamente con la interfaz ILecturaRepository.
    """

    # =================================================================
    # 1. MAPEO (ORM -> DOMINIO)
    # =================================================================
    def _map_model_to_domain(self, model: LecturaModel) -> Lectura:
        """
        Convierte datos de Django a Entidad de Dominio.
        """
        ant = float(model.lectura_anterior) if model.lectura_anterior is not None else 0.0
        consumo = float(model.consumo_del_mes) if model.consumo_del_mes is not None else 0.0

        return Lectura(
            id=model.id,
            medidor_id=model.medidor_id,
            fecha=model.fecha,
            valor=float(model.valor), 
            lectura_anterior=ant,
            consumo_del_mes_m3=consumo, 
            observacion=model.observacion,
            esta_facturada=model.esta_facturada
        )

    # =================================================================
    # 2. IMPLEMENTACIÓN DE LA INTERFAZ (ESCRITURA)
    # =================================================================
    def create(self, lectura: Lectura) -> Lectura:
        return self.save(lectura)

    def save(self, lectura: Lectura) -> Lectura:
        data_db = {
            'medidor_id': lectura.medidor_id,
            'fecha': lectura.fecha, 
            'valor': lectura.valor, 
            'lectura_anterior': lectura.lectura_anterior,
            'consumo_del_mes': getattr(lectura, 'consumo_del_mes_m3', 0),
            'observacion': lectura.observacion,
            'esta_facturada': lectura.esta_facturada
        }

        if lectura.id:
            LecturaModel.objects.filter(pk=lectura.id).update(**data_db)
        else:
            model = LecturaModel.objects.create(**data_db)
            lectura.id = model.id
        
        return lectura

    # =================================================================
    # 3. IMPLEMENTACIÓN DE LA INTERFAZ (LECTURA)
    # =================================================================
    def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        try:
            model = LecturaModel.objects.get(pk=lectura_id)
            return self._map_model_to_domain(model)
        except LecturaModel.DoesNotExist:
            return None

    # ✅ CORRECCIÓN 1: Renombrado de 'get_ultima_lectura' a 'get_latest_by_medidor'
    def get_latest_by_medidor(self, medidor_id: int) -> Optional[Lectura]:
        """
        Devuelve la lectura más reciente de un medidor.
        """
        try:
            # .latest('fecha') busca la fecha más reciente
            model = LecturaModel.objects.filter(medidor_id=medidor_id).latest('fecha')
            return self._map_model_to_domain(model)
        except LecturaModel.DoesNotExist:
            return None

    # ✅ CORRECCIÓN 2: Renombrado de 'list_by_medidor_id' a 'list_by_medidor'
    def list_by_medidor(self, medidor_id: int) -> List[Lectura]:
        """
        Devuelve el historial de lecturas.
        """
        qs = LecturaModel.objects.filter(medidor_id=medidor_id).order_by('-fecha')
        return [self._map_model_to_domain(m) for m in qs]