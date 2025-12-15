# core/use_cases/medidor_uc.py
from typing import List
from core.domain.medidor import Medidor
from core.interfaces.repositories import IMedidorRepository, ISocioRepository
from core.use_cases.medidor_dtos import MedidorDTO, CrearMedidorDTO, ActualizarMedidorDTO
from core.shared.exceptions import MedidorNoEncontradoError, SocioNoEncontradoError, ValidacionError

def _map_medidor_to_dto(medidor: Medidor) -> MedidorDTO:
    """
    Función auxiliar para convertir una Entidad de Dominio a un DTO.
    """
    return MedidorDTO(
        id=medidor.id,
        codigo=medidor.codigo,
        socio_id=medidor.socio_id,
        esta_activo=medidor.esta_activo,
        observacion=medidor.observacion,
        tiene_medidor_fisico=medidor.tiene_medidor_fisico
    )

class ListarMedidoresUseCase:
    """
    Caso de Uso para obtener la lista de todos los medidores.
    """
    def __init__(self, medidor_repo: IMedidorRepository):
        self.medidor_repo = medidor_repo

    def execute(self) -> List[MedidorDTO]:
        medidores = self.medidor_repo.list_all()
        return [_map_medidor_to_dto(m) for m in medidores]

class ObtenerMedidorUseCase:
    """
    Caso de Uso para obtener un medidor específico por su ID.
    """
    def __init__(self, medidor_repo: IMedidorRepository):
        self.medidor_repo = medidor_repo

    def execute(self, medidor_id: int) -> MedidorDTO:
        medidor = self.medidor_repo.get_by_id(medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError(f"Medidor {medidor_id} no encontrado.")
        return _map_medidor_to_dto(medidor)

class CrearMedidorUseCase:
    """
    Caso de Uso para crear un nuevo medidor.
    Valida que el socio exista y que el código sea único.
    """
    def __init__(self, medidor_repo: IMedidorRepository, socio_repo: ISocioRepository):
        self.medidor_repo = medidor_repo
        self.socio_repo = socio_repo

    def execute(self, input_dto: CrearMedidorDTO) -> MedidorDTO:
        # 1. Validar que el socio existe
        if not self.socio_repo.get_by_id(input_dto.socio_id):
            raise SocioNoEncontradoError(f"Socio {input_dto.socio_id} no encontrado.")
        
        # 2. Validar código único
        if self.medidor_repo.get_by_codigo(input_dto.codigo):
            raise ValidacionError(f"El código '{input_dto.codigo}' ya existe.")

        # 3. Crear la entidad
        medidor = Medidor(
            id=None,
            codigo=input_dto.codigo,
            socio_id=input_dto.socio_id,
            esta_activo=True,
            observacion=input_dto.observacion,
            tiene_medidor_fisico=input_dto.tiene_medidor_fisico
        )
        
        guardado = self.medidor_repo.save(medidor)
        return _map_medidor_to_dto(guardado)

class ActualizarMedidorUseCase:
    """
    Caso de Uso para actualizar un medidor existente.
    Permite actualizaciones parciales (PATCH).
    """
    def __init__(self, medidor_repo: IMedidorRepository, socio_repo: ISocioRepository):
        self.medidor_repo = medidor_repo
        self.socio_repo = socio_repo

    def execute(self, medidor_id: int, input_dto: ActualizarMedidorDTO) -> MedidorDTO:
        # 1. Buscar el medidor existente
        medidor = self.medidor_repo.get_by_id(medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError(f"Medidor {medidor_id} no encontrado.")

        # 2. Actualizar campos si vienen en el DTO
        if input_dto.socio_id is not None:
            # Si cambiamos el dueño, verificamos que el nuevo exista
            if not self.socio_repo.get_by_id(input_dto.socio_id):
                raise SocioNoEncontradoError(f"Socio {input_dto.socio_id} no encontrado.")
            medidor.socio_id = input_dto.socio_id

        if input_dto.codigo is not None:
            # Si cambiamos el código, verificamos que no esté duplicado
            existente = self.medidor_repo.get_by_codigo(input_dto.codigo)
            # El código puede existir si es ESTE MISMO medidor
            if existente and existente.id != medidor_id:
                raise ValidacionError(f"El código '{input_dto.codigo}' ya está en uso.")
            medidor.codigo = input_dto.codigo

        if input_dto.esta_activo is not None: 
            medidor.esta_activo = input_dto.esta_activo
        
        if input_dto.observacion is not None: 
            medidor.observacion = input_dto.observacion
            
        if input_dto.tiene_medidor_fisico is not None: 
            medidor.tiene_medidor_fisico = input_dto.tiene_medidor_fisico

        # 3. Guardar cambios
        guardado = self.medidor_repo.save(medidor)
        return _map_medidor_to_dto(guardado)

class EliminarMedidorUseCase:
    """
    Caso de Uso para eliminar (lógicamente) un medidor.
    """
    def __init__(self, medidor_repo: IMedidorRepository):
        self.medidor_repo = medidor_repo

    def execute(self, medidor_id: int) -> None:
        medidor = self.medidor_repo.get_by_id(medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError(f"Medidor {medidor_id} no encontrado.")
        
        # Soft Delete (Desactivación lógica)
        medidor.esta_activo = False
        self.medidor_repo.save(medidor)