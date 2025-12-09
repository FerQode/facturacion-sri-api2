# core/use_cases/socio_uc.py
from typing import List, Optional
from core.domain.socio import Socio
# --- AÑADIDO: Importamos el repositorio de Autenticación ---
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
        barrio=socio.barrio,
        rol=socio.rol.value,
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
    """
    Caso de Uso que orquesta la creación de un Socio y su
    cuenta de Usuario (Auth) correspondiente.
    """
    def __init__(self, socio_repo: ISocioRepository, auth_repo: IAuthRepository):
        self.socio_repo = socio_repo
        self.auth_repo = auth_repo

    def execute(self, input_dto: CrearSocioDTO) -> SocioDTO:
        if self.socio_repo.get_by_cedula(input_dto.cedula):
            raise ValidacionError(f"La cédula {input_dto.cedula} ya está registrada.")
        
        username = input_dto.username if input_dto.username else input_dto.cedula
        password = input_dto.password if input_dto.password else input_dto.cedula

        try:
            usuario_id = self.auth_repo.crear_usuario(
                username=username, 
                password=password, 
                email=input_dto.email,
                rol=input_dto.rol 
            )
        except ValueError as e:
            raise ValidacionError(f"Error al crear usuario: {str(e)}")

        # --- CORRECCIÓN AQUÍ: Usamos argumentos con nombre ---
        socio_entidad = Socio(
            id=None,
            cedula=input_dto.cedula,
            nombres=input_dto.nombres,
            apellidos=input_dto.apellidos,
            barrio=input_dto.barrio,
            rol=input_dto.rol,
            email=input_dto.email,
            telefono=input_dto.telefono,
            esta_activo=True,
            usuario_id=usuario_id # Campo opcional al final
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

        # 2. Actualizar solo los campos que vienen en el DTO (lógica de "parcheo")
        if input_dto.nombres is not None: socio_entidad.nombres = input_dto.nombres
        if input_dto.apellidos is not None: socio_entidad.apellidos = input_dto.apellidos
        if input_dto.barrio is not None: socio_entidad.barrio = input_dto.barrio
        if input_dto.rol is not None: socio_entidad.rol = input_dto.rol
        if input_dto.email is not None: socio_entidad.email = input_dto.email
        if input_dto.telefono is not None: socio_entidad.telefono = input_dto.telefono
        
        # 3. Lógica de Reactivación/Desactivación (Gestión de Usuario)
        if input_dto.esta_activo is not None:
            # Caso A: Reactivación (False -> True)
            if input_dto.esta_activo and not socio_entidad.esta_activo:
                if socio_entidad.usuario_id:
                    # ¡AQUÍ ESTÁ LA CLAVE! Llamamos a activar_usuario
                    # Este método solo pone is_active=True, NO toca la contraseña.
                    self.auth_repo.activar_usuario(socio_entidad.usuario_id)
            
            # Caso B: Desactivación (True -> False)
            elif not input_dto.esta_activo and socio_entidad.esta_activo:
                if socio_entidad.usuario_id:
                    self.auth_repo.desactivar_usuario(socio_entidad.usuario_id)
            
            # Actualizamos el estado en el objeto Socio
            socio_entidad.esta_activo = input_dto.esta_activo
        
        # 4. Guardar los cambios del Socio
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
        
        # 1. Desactivar el Socio (Soft Delete)
        socio.esta_activo = False
        self.socio_repo.save(socio)
        
        # 2. Desactivar el Usuario vinculado (para que no pueda loguearse)
        if socio.usuario_id:
            self.auth_repo.desactivar_usuario(socio.usuario_id) 