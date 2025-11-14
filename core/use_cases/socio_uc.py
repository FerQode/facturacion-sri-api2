# core/use_cases/socio_uc.py
from typing import List, Optional
from core.domain.socio import Socio
from core.interfaces.repositories import ISocioRepository
from core.use_cases.socio_dtos import SocioDTO, CrearSocioDTO, ActualizarSocioDTO
from core.shared.exceptions import SocioNoEncontradoError, ValidacionError

# Función helper para traducir Entidad -> DTO
def _map_socio_to_dto(socio: Socio) -> SocioDTO:
    return SocioDTO(
        id=socio.id,
        cedula=socio.cedula,
        nombres=socio.nombres,
        apellidos=socio.apellidos,
        email=socio.email,
        telefono=socio.telefono,
        barrio=socio.barrio,
        rol=socio.rol.value, # Convertimos Enum a string
        esta_activo=socio.esta_activo
    )

class ListarSociosUseCase:
    def __init__(self, socio_repo: ISocioRepository):
        self.socio_repo = socio_repo

    def execute(self) -> List[SocioDTO]:
        socios = self.socio_repo.list_all()
        return [_map_socio_to_dto(socio) for socio in socios]

class ObtenerSocioUseCase:
    def __init__(self, socio_repo: ISocioRepository):
        self.socio_repo = socio_repo

    def execute(self, socio_id: int) -> SocioDTO:
        socio = self.socio_repo.get_by_id(socio_id)
        if not socio:
            raise SocioNoEncontradoError(f"Socio con id {socio_id} no encontrado.")
        return _map_socio_to_dto(socio)

class CrearSocioUseCase:
    def __init__(self, socio_repo: ISocioRepository):
        self.socio_repo = socio_repo

    def execute(self, input_dto: CrearSocioDTO) -> SocioDTO:
        # 1. Validar reglas de negocio (ej: cédula única)
        if self.socio_repo.get_by_cedula(input_dto.cedula):
            raise ValidacionError(f"La cédula {input_dto.cedula} ya está registrada.")
        
        # 2. Crear la Entidad de dominio
        socio_entidad = Socio(
            id=None, # La BBDD lo asignará
            cedula=input_dto.cedula,
            nombres=input_dto.nombres,
            apellidos=input_dto.apellidos,
            barrio=input_dto.barrio,
            rol=input_dto.rol,
            email=input_dto.email,
            telefono=input_dto.telefono,
            esta_activo=True
        )
        
        # 3. Guardar usando el repositorio
        socio_guardado = self.socio_repo.save(socio_entidad)
        return _map_socio_to_dto(socio_guardado)

class ActualizarSocioUseCase:
    def __init__(self, socio_repo: ISocioRepository):
        self.socio_repo = socio_repo

    def execute(self, socio_id: int, input_dto: ActualizarSocioDTO) -> SocioDTO:
        # 1. Obtener la entidad existente
        socio_entidad = self.socio_repo.get_by_id(socio_id)
        if not socio_entidad:
            raise SocioNoEncontradoError(f"Socio con id {socio_id} no encontrado.")

        # 2. Actualizar solo los campos que vienen en el DTO (lógica de "parcheo")
        if input_dto.nombres is not None:
            socio_entidad.nombres = input_dto.nombres
        if input_dto.apellidos is not None:
            socio_entidad.apellidos = input_dto.apellidos
        if input_dto.barrio is not None:
            socio_entidad.barrio = input_dto.barrio
        if input_dto.rol is not None:
            socio_entidad.rol = input_dto.rol
        if input_dto.email is not None:
            socio_entidad.email = input_dto.email
        if input_dto.telefono is not None:
            socio_entidad.telefono = input_dto.telefono
        if input_dto.esta_activo is not None:
            socio_entidad.esta_activo = input_dto.esta_activo
        
        # 3. Guardar los cambios
        socio_actualizado = self.socio_repo.save(socio_entidad)
        return _map_socio_to_dto(socio_actualizado)

class EliminarSocioUseCase:
    def __init__(self, socio_repo: ISocioRepository):
        self.socio_repo = socio_repo

    def execute(self, socio_id: int) -> None:
        socio = self.socio_repo.get_by_id(socio_id)
        if not socio:
            raise SocioNoEncontradoError(f"Socio con id {socio_id} no encontrado.")
        
        # Buena Práctica: No borramos, "desactivamos" (Soft Delete)
        socio.esta_activo = False
        self.socio_repo.save(socio)