# adapters/infrastructure/repositories/django_terreno_repository.py

from typing import List, Optional
from django.db import transaction, IntegrityError

# 1. Imports de Core (Contratos y Dominio)
from core.interfaces.repositories import ITerrenoRepository
from core.domain.terreno import Terreno
from core.domain.medidor import Medidor
from core.shared.exceptions import MedidorDuplicadoError

# 2. Imports de Infraestructura (Modelos Django)
from adapters.infrastructure.models.terreno_model import TerrenoModel
from adapters.infrastructure.models.medidor_model import MedidorModel
# Importamos Barrio y Socio solo si necesitamos validaciones extra, 
# pero Django permite asignar por ID directo usando 'barrio_id' y 'socio_id' en el constructor.

class DjangoTerrenoRepository(ITerrenoRepository):
    """
    Implementación del repositorio de Terrenos usando el ORM de Django.
    Actúa como adaptador entre el Dominio (Objetos Puros) y la Base de Datos (Tablas).
    """

    def create(self, terreno: Terreno) -> Terreno:
        """
        Crea un nuevo terreno y opcionalmente su medidor en una transacción atómica.
        Alias para save() en contexto de creación.
        """
        return self.save(terreno)

    def save(self, terreno: Terreno) -> Terreno:
        """
        Persiste un objeto de dominio Terreno en la base de datos.
        Maneja la creación del registro en 'terrenos' y, si corresponde, en 'medidores'.
        """
        try:
            with transaction.atomic():
                # 1. Mapeo Dominio -> Modelo Django (Terreno)
                # Usamos los _id directos para eficiencia (Django lo permite)
                terreno_model = TerrenoModel(
                    socio_id=terreno.socio_id,
                    barrio_id=terreno.barrio_id,
                    direccion=terreno.direccion,
                    es_cometida_activa=terreno.es_cometida_activa
                )
                
                # 2. Guardar Terreno (Genera el ID en BBDD)
                terreno_model.save()
                
                # Actualizamos el ID del objeto de dominio con el generado por la BD
                terreno.id = terreno_model.id

                # 3. Verificar si el Dominio trae un Medidor para crear
                # Nota: En tu Caso de Uso (RegistrarTerrenoUseCase), el medidor se crea APARTE
                # llamando a MedidorRepository.create(). 
                # Sin embargo, si quisieras guardar todo junto aquí, se haría así.
                # PERO, respetando tu Caso de Uso actual, este método save() 
                # se enfoca en persistir el Terreno correctamente.
                
                # Convertimos el modelo guardado de vuelta a Dominio para retornar datos frescos
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
        """
        Implementación: SELECT * FROM terrenos WHERE barrio_id = X
        """
        # Usamos select_related para optimizar y traer el nombre del barrio en 1 sola consulta
        qs = TerrenoModel.objects.select_related('barrio').filter(barrio_id=barrio_id)
        return [self._map_model_to_domain(model) for model in qs]

    # --- MÉTODOS AUXILIARES DE MAPEO ---

    def _map_model_to_domain(self, model: TerrenoModel) -> Terreno:
        """
        Convierte un TerrenoModel (Django) a Terreno (Dominio).
        """
        return Terreno(
            id=model.id,
            socio_id=model.socio_id,
            barrio_id=model.barrio_id,
            direccion=model.direccion,
            es_cometida_activa=model.es_cometida_activa,
            # Campos opcionales enriquecidos
            nombre_barrio=model.barrio.nombre if model.barrio else None,
            # nombre_socio podría agregarse si el dominio lo tiene
        )