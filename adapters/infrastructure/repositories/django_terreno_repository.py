# adapters/infrastructure/repositories/django_terreno_repository.py

from typing import List, Optional
from django.db import transaction, IntegrityError

# 1. Imports de Core (Contratos y Dominio)
from core.interfaces.repositories import ITerrenoRepository
from core.domain.terreno import Terreno

# 2. Imports de Infraestructura (Modelos Django)
from adapters.infrastructure.models.terreno_model import TerrenoModel

class DjangoTerrenoRepository(ITerrenoRepository):
    """
    Implementación del repositorio de Terrenos usando el ORM de Django.
    Actúa como adaptador entre el Dominio (Objetos Puros) y la Base de Datos (Tablas).
    """

    def create(self, terreno: Terreno) -> Terreno:
        return self.save(terreno)

    def save(self, terreno: Terreno) -> Terreno:
        """
        Persiste un objeto de dominio Terreno en la base de datos.
        CORREGIDO: Detecta si es INSERT o UPDATE para evitar duplicados.
        """
        try:
            with transaction.atomic():
                terreno_model = None

                # 1. INTENTO DE UPDATE (Si el objeto ya tiene ID)
                if terreno.id:
                    try:
                        terreno_model = TerrenoModel.objects.get(id=terreno.id)
                        # Actualizamos campos explícitamente
                        terreno_model.socio_id = terreno.socio_id
                        terreno_model.barrio_id = terreno.barrio_id
                        terreno_model.direccion = terreno.direccion
                        terreno_model.es_cometida_activa = terreno.es_cometida_activa
                        # Guardamos sobre el registro existente
                        terreno_model.save()
                    except TerrenoModel.DoesNotExist:
                        pass # Si no existe, pasamos a crear
                
                # 2. INTENTO DE INSERT (Si no tenía ID o no se encontró)
                if not terreno_model:
                    terreno_model = TerrenoModel(
                        socio_id=terreno.socio_id,
                        barrio_id=terreno.barrio_id,
                        direccion=terreno.direccion,
                        es_cometida_activa=terreno.es_cometida_activa
                    )
                    terreno_model.save()
                
                # Actualizamos el ID del objeto de dominio
                terreno.id = terreno_model.id
                
                return self._map_model_to_domain(terreno_model)

        except Exception as e:
            # Aquí podrías loguear el error real
            raise e

    def get_by_id(self, terreno_id: int) -> Optional[Terreno]:
        try:
            terreno_model = TerrenoModel.objects.get(id=terreno_id)
            return self._map_model_to_domain(terreno_model)
        except TerrenoModel.DoesNotExist:
            return None

    def list_by_socio_id(self, socio_id: int) -> List[Terreno]:
        qs = TerrenoModel.objects.filter(socio_id=socio_id)
        return [self._map_model_to_domain(model) for model in qs]
    
    def list_by_barrio_id(self, barrio_id: int) -> List[Terreno]:
        qs = TerrenoModel.objects.select_related('barrio').filter(barrio_id=barrio_id)
        return [self._map_model_to_domain(model) for model in qs]

    def get_by_socio(self, socio_id: int) -> List[Terreno]:
        qs = TerrenoModel.objects.select_related('barrio').filter(socio_id=socio_id)
        return [self._map_model_to_domain(model) for model in qs]

    # --- MÉTODOS AUXILIARES DE MAPEO ---

    def _map_model_to_domain(self, model: TerrenoModel) -> Terreno:
        return Terreno(
            id=model.id,
            socio_id=model.socio_id,
            barrio_id=model.barrio_id,
            direccion=model.direccion,
            es_cometida_activa=model.es_cometida_activa,
            nombre_barrio=model.barrio.nombre if model.barrio else None,
        )