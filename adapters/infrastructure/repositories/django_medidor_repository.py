# adapters/infrastructure/repositories/django_medidor_repository.py

from typing import List, Optional
from django.db import IntegrityError

# Imports de Core
from core.interfaces.repositories import IMedidorRepository
from core.domain.medidor import Medidor
from core.shared.exceptions import MedidorDuplicadoError

# Imports de Infraestructura
from adapters.infrastructure.models.medidor_model import MedidorModel

class DjangoMedidorRepository(IMedidorRepository):
    """
    Implementación del Repositorio de Medidores usando el ORM de Django.
    Actualizado para Clean Architecture (Fase 3).
    """

    def _to_entity(self, model: MedidorModel) -> Medidor:
        """
        Mapeador: Modelo de Django -> Entidad de Dominio
        ACTUALIZADO: Refleja la nueva estructura vinculada a Terrenos.
        """
        return Medidor(
            id=model.id,
            # CLAVE: Ahora el medidor pertenece a un terreno, no directamente al socio
            terreno_id=model.terreno_id, 
            codigo=model.codigo,
            marca=model.marca,
            # Convertimos Decimal a float para el dominio, si es necesario
            lectura_inicial=float(model.lectura_inicial),
            # El estado ahora es un string ('ACTIVO', 'INACTIVO', etc.)
            estado=model.estado, 
            observacion=model.observacion,
            fecha_instalacion=model.fecha_instalacion
        )

    # --- IMPLEMENTACIÓN DE LA INTERFAZ ---

    def create(self, medidor: Medidor) -> Medidor:
        """Método explícito de creación."""
        return self.save(medidor)

    def save(self, medidor: Medidor) -> Medidor:
        """
        Guarda o actualiza un medidor en la base de datos.
        Maneja errores de duplicidad de código.
        """
        try:
            if medidor.id:
                # CASO 1: Actualizar existente
                try:
                    model = MedidorModel.objects.get(pk=medidor.id)
                except MedidorModel.DoesNotExist:
                    # Si viene con ID pero no existe en BD, intentamos crearlo
                    model = MedidorModel()
            else:
                # CASO 2: Crear nuevo
                model = MedidorModel()

            # Asignación de campos (Mapping inverso: Entidad -> Modelo)
            model.terreno_id = medidor.terreno_id
            model.codigo = medidor.codigo
            model.marca = medidor.marca
            model.lectura_inicial = medidor.lectura_inicial
            model.estado = medidor.estado
            model.observacion = medidor.observacion
            
            # Guardamos en BBDD
            model.save()
            
            # Actualizamos el ID de la entidad y la retornamos
            medidor.id = model.id
            return self._to_entity(model)

        except IntegrityError:
            # Si la BBDD grita porque el código ya existe, lanzamos error de negocio
            raise MedidorDuplicadoError(f"El medidor con código '{medidor.codigo}' ya está registrado.")

    def get_by_id(self, medidor_id: int) -> Optional[Medidor]:
        try:
            model = MedidorModel.objects.get(pk=medidor_id)
            return self._to_entity(model)
        except MedidorModel.DoesNotExist:
            return None

    def get_by_codigo(self, codigo: str) -> Optional[Medidor]:
        try:
            model = MedidorModel.objects.get(codigo=codigo)
            return self._to_entity(model)
        except MedidorModel.DoesNotExist:
            return None

    def get_by_terreno_id(self, terreno_id: int) -> Optional[Medidor]:
        """
        NUEVO MÉTODO: Obtiene el medidor instalado en un terreno específico.
        """
        try:
            model = MedidorModel.objects.get(terreno_id=terreno_id)
            return self._to_entity(model)
        except MedidorModel.DoesNotExist:
            return None

    def list_all(self) -> List[Medidor]:
        """Lista TODOS los medidores del sistema."""
        models = MedidorModel.objects.all()
        return [self._to_entity(m) for m in models]