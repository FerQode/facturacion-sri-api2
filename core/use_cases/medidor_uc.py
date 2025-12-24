# core/use_cases/medidor_uc.py

from typing import List, Optional
from core.domain.medidor import Medidor
from core.interfaces.repositories import IMedidorRepository, ITerrenoRepository
# CORRECCIÓN: Usamos los DTOs actualizados
from core.use_cases.medidor_dtos import (
    MedidorDTO, 
    RegistrarMedidorDTO, 
    ActualizarMedidorDTO
)
from core.shared.exceptions import (
    MedidorNoEncontradoError, 
    EntityNotFoundException, 
    BusinessRuleException, 
    MedidorDuplicadoError
)

def _map_medidor_to_dto(medidor: Medidor) -> MedidorDTO:
    """
    Función auxiliar para convertir Entidad de Dominio -> DTO de Salida.
    """
    return MedidorDTO(
        id=medidor.id,
        terreno_id=medidor.terreno_id, # Ahora vinculado a Terreno
        codigo=medidor.codigo,
        marca=medidor.marca,
        lectura_inicial=medidor.lectura_inicial,
        estado=medidor.estado, # 'ACTIVO', 'INACTIVO', etc.
        observacion=medidor.observacion,
        fecha_instalacion=str(medidor.fecha_instalacion) if medidor.fecha_instalacion else None
    )

class ListarMedidoresUseCase:
    """Obtiene todos los medidores."""
    def __init__(self, medidor_repo: IMedidorRepository):
        self.medidor_repo = medidor_repo

    def execute(self) -> List[MedidorDTO]:
        medidores = self.medidor_repo.list_all()
        return [_map_medidor_to_dto(m) for m in medidores]

class ObtenerMedidorUseCase:
    """Obtiene un medidor por ID."""
    def __init__(self, medidor_repo: IMedidorRepository):
        self.medidor_repo = medidor_repo

    def execute(self, medidor_id: int) -> MedidorDTO:
        medidor = self.medidor_repo.get_by_id(medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError(f"Medidor {medidor_id} no encontrado.")
        return _map_medidor_to_dto(medidor)

class CrearMedidorUseCase:
    """
    Crea un medidor nuevo vinculado a un Terreno.
    """
    def __init__(self, medidor_repo: IMedidorRepository, terreno_repo: ITerrenoRepository):
        self.medidor_repo = medidor_repo
        self.terreno_repo = terreno_repo

    def execute(self, dto: RegistrarMedidorDTO) -> MedidorDTO:
        # 1. Validar Terreno
        if not self.terreno_repo.get_by_id(dto.terreno_id):
            raise EntityNotFoundException(f"El terreno {dto.terreno_id} no existe.")

        # 2. Validar Unicidad de Código
        if self.medidor_repo.get_by_codigo(dto.codigo):
            raise MedidorDuplicadoError(f"El código '{dto.codigo}' ya existe.")
        
        # 3. Validar que el terreno no tenga ya un medidor activo
        # (Opcional, depende de tu regla de negocio, pero recomendado)
        if self.medidor_repo.get_by_terreno_id(dto.terreno_id):
             raise BusinessRuleException("Este terreno ya tiene un medidor instalado.")

        # 4. Crear Entidad
        medidor = Medidor(
            id=None,
            terreno_id=dto.terreno_id,
            codigo=dto.codigo,
            marca=dto.marca,
            lectura_inicial=dto.lectura_inicial,
            estado='ACTIVO',
            observacion=dto.observacion
        )
        
        guardado = self.medidor_repo.save(medidor)
        return _map_medidor_to_dto(guardado)

class ActualizarMedidorUseCase:
    """
    Actualiza datos básicos (corrección de errores).
    """
    def __init__(self, medidor_repo: IMedidorRepository):
        self.medidor_repo = medidor_repo

    def execute(self, medidor_id: int, dto: ActualizarMedidorDTO) -> MedidorDTO:
        medidor = self.medidor_repo.get_by_id(medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError(f"Medidor {medidor_id} no encontrado.")

        # Solo permitimos corregir campos visuales, NO estructurales
        if dto.codigo:
            # Validar unicidad si cambia el código
            existente = self.medidor_repo.get_by_codigo(dto.codigo)
            if existente and existente.id != medidor_id:
                raise MedidorDuplicadoError(f"El código '{dto.codigo}' ya está en uso.")
            medidor.codigo = dto.codigo

        if dto.marca:
            medidor.marca = dto.marca
        
        if dto.observacion:
            medidor.observacion = dto.observacion

        guardado = self.medidor_repo.save(medidor)
        return _map_medidor_to_dto(guardado)

class EliminarMedidorUseCase:
    """
    Desactiva un medidor (Soft Delete).
    Nota: Para cambios reales, usar ReemplazarMedidorUseCase.
    """
    def __init__(self, medidor_repo: IMedidorRepository):
        self.medidor_repo = medidor_repo

    def execute(self, medidor_id: int) -> None:
        medidor = self.medidor_repo.get_by_id(medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError(f"Medidor {medidor_id} no encontrado.")
        
        medidor.estado = 'INACTIVO'
        # Desvincular del terreno para liberar el cupo (Opcional, según negocio)
        # medidor.terreno_id = None 
        
        self.medidor_repo.save(medidor)