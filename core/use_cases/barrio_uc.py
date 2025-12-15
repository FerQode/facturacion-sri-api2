# core/use_cases/barrio_uc.py
from typing import List, Optional
from core.domain.barrio import Barrio
from core.interfaces.repositories import IBarrioRepository
from core.use_cases.barrio_dtos import BarrioDTO, CrearBarrioDTO, ActualizarBarrioDTO
from core.shared.exceptions import ValidacionError, BaseExcepcionDeNegocio

# Excepción específica para Barrio no encontrado (puedes moverla a exceptions.py si prefieres)
class BarrioNoEncontradoError(BaseExcepcionDeNegocio):
    pass

def _map_barrio_to_dto(barrio: Barrio) -> BarrioDTO:
    """Helper para convertir Entidad -> DTO"""
    return BarrioDTO(
        id=barrio.id,
        nombre=barrio.nombre,
        descripcion=barrio.descripcion,
        activo=barrio.activo
    )

class ListarBarriosUseCase:
    """
    Caso de Uso para obtener la lista de todos los barrios.
    Útil para llenar los selects en el frontend.
    """
    def __init__(self, barrio_repo: IBarrioRepository):
        self.barrio_repo = barrio_repo

    def execute(self) -> List[BarrioDTO]:
        barrios = self.barrio_repo.list_all()
        return [_map_barrio_to_dto(b) for b in barrios]

class ObtenerBarrioUseCase:
    """
    Caso de Uso para obtener un barrio específico por su ID.
    """
    def __init__(self, barrio_repo: IBarrioRepository):
        self.barrio_repo = barrio_repo

    def execute(self, barrio_id: int) -> BarrioDTO:
        barrio = self.barrio_repo.get_by_id(barrio_id)
        if not barrio:
            raise BarrioNoEncontradoError(f"Barrio con id {barrio_id} no encontrado.")
        return _map_barrio_to_dto(barrio)

class CrearBarrioUseCase:
    """
    Caso de Uso para crear un nuevo barrio.
    Valida que el nombre sea único.
    """
    def __init__(self, barrio_repo: IBarrioRepository):
        self.barrio_repo = barrio_repo

    def execute(self, input_dto: CrearBarrioDTO) -> BarrioDTO:
        # 1. Validar nombre único (Regla de Negocio)
        if self.barrio_repo.get_by_nombre(input_dto.nombre):
            raise ValidacionError(f"El barrio '{input_dto.nombre}' ya existe.")

        # 2. Crear entidad
        barrio = Barrio(
            id=None,
            nombre=input_dto.nombre,
            descripcion=input_dto.descripcion,
            activo=input_dto.activo
        )
        
        # 3. Guardar
        guardado = self.barrio_repo.save(barrio)
        return _map_barrio_to_dto(guardado)

class ActualizarBarrioUseCase:
    """
    Caso de Uso para actualizar un barrio existente.
    Permite actualizaciones parciales.
    """
    def __init__(self, barrio_repo: IBarrioRepository):
        self.barrio_repo = barrio_repo

    def execute(self, barrio_id: int, input_dto: ActualizarBarrioDTO) -> BarrioDTO:
        # 1. Obtener barrio actual
        barrio = self.barrio_repo.get_by_id(barrio_id)
        if not barrio:
            raise BarrioNoEncontradoError(f"Barrio con id {barrio_id} no encontrado.")

        # 2. Validar cambio de nombre (si aplica)
        if input_dto.nombre is not None and input_dto.nombre != barrio.nombre:
            existente = self.barrio_repo.get_by_nombre(input_dto.nombre)
            if existente and existente.id != barrio_id:
                raise ValidacionError(f"El nombre '{input_dto.nombre}' ya está en uso por otro barrio.")
            barrio.nombre = input_dto.nombre

        # 3. Actualizar otros campos
        if input_dto.descripcion is not None: 
            barrio.descripcion = input_dto.descripcion
        
        if input_dto.activo is not None:
            barrio.activo = input_dto.activo

        # 4. Guardar
        guardado = self.barrio_repo.save(barrio)
        return _map_barrio_to_dto(guardado)

class EliminarBarrioUseCase:
    """
    Caso de Uso para eliminar un barrio.
    Por ahora implementamos Soft Delete (desactivación).
    En el futuro, podríamos validar si tiene socios asociados antes de permitir borrar.
    """
    def __init__(self, barrio_repo: IBarrioRepository):
        self.barrio_repo = barrio_repo

    def execute(self, barrio_id: int) -> None:
        barrio = self.barrio_repo.get_by_id(barrio_id)
        if not barrio:
            raise BarrioNoEncontradoError(f"Barrio con id {barrio_id} no encontrado.")
        
        # Soft Delete: Solo desactivamos para no romper integridad referencial
        # si ya hay socios viviendo en este barrio.
        barrio.activo = False
        self.barrio_repo.save(barrio)