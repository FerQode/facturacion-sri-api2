# adapters/infrastructure/repositories/django_lectura_repository.py

from typing import List, Optional
from core.interfaces.repositories import ILecturaRepository
from core.domain.lectura import Lectura
from adapters.infrastructure.models import LecturaModel

class DjangoLecturaRepository(ILecturaRepository):
    """
    Implementación del Repositorio de Lecturas usando Django ORM.
    CORREGIDO: Alineado exactamente con core/domain/lectura.py
    """

    def _to_entity(self, model: LecturaModel) -> Lectura:
        """
        Mapea ORM (Base de Datos) -> Entidad (Dominio).
        """
        # Manejo de nulos para lectura_anterior
        ant = float(model.lectura_anterior) if model.lectura_anterior is not None else 0.0
        
        # Manejo de consumo
        consumo = float(model.consumo_del_mes) if model.consumo_del_mes is not None else 0.0

        return Lectura(
            id=model.id,
            medidor_id=model.medidor_id,
            
            # --- CORRECCIÓN DE NOMBRES ---
            # Usamos 'fecha' porque así se llama en tu Entidad de Dominio
            fecha=model.fecha, 
            
            # Usamos 'valor' porque así se llama en tu Entidad de Dominio
            valor=float(model.valor), 
            
            lectura_anterior=ant,
            consumo_del_mes_m3=consumo,
            
            observacion=model.observacion,
            esta_facturada=model.esta_facturada
        )

    def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        try:
            model = LecturaModel.objects.get(pk=lectura_id)
            return self._to_entity(model)
        except LecturaModel.DoesNotExist:
            return None

    def get_latest_by_medidor(self, medidor_id: int) -> Optional[Lectura]:
        try:
            # .latest() usa el 'get_latest_by' del Meta del modelo ('fecha')
            model = LecturaModel.objects.filter(medidor_id=medidor_id).latest()
            return self._to_entity(model)
        except LecturaModel.DoesNotExist:
            return None

    # --- EL MÉTODO QUE FALTABA Y CAUSABA EL ERROR 500 ---
    def list_by_medidor(self, medidor_id: int, limit: int = 12) -> List[Lectura]:
        """
        Obtiene el historial de lecturas de un medidor.
        """
        models = LecturaModel.objects.filter(medidor_id=medidor_id).order_by('-fecha')[:limit]
        return [self._to_entity(m) for m in models]

    def save(self, lectura: Lectura) -> Lectura:
        """
        Guarda o actualiza la Entidad en la BBDD.
        """
        # Mapeo Inverso: Dominio -> Base de Datos
        data_db = {
            'medidor_id': lectura.medidor_id,
            
            # Mapeo exacto: Entidad.fecha -> Modelo.fecha
            'fecha': lectura.fecha, 
            
            # Mapeo exacto: Entidad.valor -> Modelo.valor
            'valor': lectura.valor, 
            
            'lectura_anterior': lectura.lectura_anterior,
            'consumo_del_mes': lectura.consumo_del_mes_m3,
            
            'observacion': lectura.observacion,
            'esta_facturada': lectura.esta_facturada
        }

        if lectura.id:
            # UPDATE
            LecturaModel.objects.filter(pk=lectura.id).update(**data_db)
            # No es necesario recargar el objeto
        else:
            # CREATE
            model = LecturaModel.objects.create(**data_db)
            lectura.id = model.id
        
        return lectura