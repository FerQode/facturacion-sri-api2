# core/use_cases/socio_uc.py
from typing import List, Optional
from core.domain.socio import Socio
from core.interfaces.repositories import ISocioRepository, IAuthRepository
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
        
        # --- CORRECCIÓN: Usamos barrio_id ---
        barrio_id=socio.barrio_id, 
        direccion=socio.direccion, # Agregamos dirección si el DTO lo soporta
        # ------------------------------------
        
        rol=socio.rol.value if socio.rol else None,
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
    def __init__(self, socio_repo: ISocioRepository, auth_repo: IAuthRepository):
        self.socio_repo = socio_repo
        self.auth_repo = auth_repo

    def execute(self, input_dto: CrearSocioDTO) -> SocioDTO:
        # 1. Validar duplicados
        if self.socio_repo.get_by_cedula(input_dto.cedula):
            raise ValidacionError(f"La cédula {input_dto.cedula} ya está registrada.")
        
        # 2. Configurar credenciales por defecto (Cédula/Cédula)
        username = input_dto.username if input_dto.username else input_dto.cedula
        password = input_dto.password if input_dto.password else input_dto.cedula

        try:
            # 3. Crear Usuario en Auth (Sistema de Login)
            usuario_id = self.auth_repo.crear_usuario(
                username=username, 
                password=password, 
                email=input_dto.email,
                rol=input_dto.rol 
            )
        except ValueError as e:
            raise ValidacionError(f"Error al crear usuario: {str(e)}")

        # 4. Crear Entidad Socio
        socio_entidad = Socio(
            id=None,
            cedula=input_dto.cedula,
            nombres=input_dto.nombres,
            apellidos=input_dto.apellidos,
            
            # --- CORRECCIÓN: Mapeamos barrio_id ---
            barrio_id=input_dto.barrio_id, # El DTO debe traer este campo int
            direccion=input_dto.direccion,
            # --------------------------------------
            
            rol=input_dto.rol,
            email=input_dto.email,
            telefono=input_dto.telefono,
            esta_activo=True,
            usuario_id=usuario_id
        )
        
        socio_guardado = self.socio_repo.save(socio_entidad)
        return _map_socio_to_dto(socio_guardado)

class ActualizarSocioUseCase:
    def __init__(self, socio_repo: ISocioRepository, auth_repo: IAuthRepository):
        self.socio_repo = socio_repo
        self.auth_repo = auth_repo

    def execute(self, socio_id: int, input_dto: ActualizarSocioDTO) -> SocioDTO:
        # 1. Obtener la entidad existente
        socio_entidad = self.socio_repo.get_by_id(socio_id)
        if not socio_entidad:
            raise SocioNoEncontradoError(f"Socio con id {socio_id} no encontrado.")

        # 2. Actualizar solo los campos que vienen en el DTO
        if input_dto.nombres is not None: socio_entidad.nombres = input_dto.nombres
        if input_dto.apellidos is not None: socio_entidad.apellidos = input_dto.apellidos
        
        # --- CORRECCIÓN: barrio_id ---
        if input_dto.barrio_id is not None: socio_entidad.barrio_id = input_dto.barrio_id
        if input_dto.direccion is not None: socio_entidad.direccion = input_dto.direccion
        # -----------------------------

        if input_dto.rol is not None: socio_entidad.rol = input_dto.rol
        if input_dto.email is not None: socio_entidad.email = input_dto.email
        if input_dto.telefono is not None: socio_entidad.telefono = input_dto.telefono
        
        # 3. Lógica de Reactivación/Desactivación
        if input_dto.esta_activo is not None:
            if input_dto.esta_activo and not socio_entidad.esta_activo:
                if socio_entidad.usuario_id:
                    self.auth_repo.activar_usuario(socio_entidad.usuario_id)
            elif not input_dto.esta_activo and socio_entidad.esta_activo:
                if socio_entidad.usuario_id:
                    self.auth_repo.desactivar_usuario(socio_entidad.usuario_id)
            
            socio_entidad.esta_activo = input_dto.esta_activo
        
        # 4. Guardar
        socio_actualizado = self.socio_repo.save(socio_entidad)
        return _map_socio_to_dto(socio_actualizado)

class EliminarSocioUseCase:
    def __init__(self, socio_repo: ISocioRepository, auth_repo: IAuthRepository):
        self.socio_repo = socio_repo
        self.auth_repo = auth_repo

    def execute(self, socio_id: int) -> None:
        socio = self.socio_repo.get_by_id(socio_id)
        if not socio:
            raise SocioNoEncontradoError(f"Socio con id {socio_id} no encontrado.")
        
        # Soft Delete
        socio.esta_activo = False
        self.socio_repo.save(socio)
        
        if socio.usuario_id:
            self.auth_repo.desactivar_usuario(socio.usuario_id)