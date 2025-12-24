# core/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

# Importamos nuestras Entidades de Dominio
from core.domain.socio import Socio
from core.domain.medidor import Medidor
from core.domain.lectura import Lectura
from core.domain.factura import Factura
from core.domain.barrio import Barrio 
from core.domain.terreno import Terreno # <--- [NUEVO] Importamos la entidad Terreno
from core.shared.enums import EstadoFactura, RolUsuario

"""
Interfaces de Repositorio:
Definen los contratos que la capa de Casos de Uso (Use Cases)
utilizará para interactuar con la base de datos.
"""

class ISocioRepository(ABC):
    
    @abstractmethod
    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        """Obtiene un socio por su ID."""
        pass

    @abstractmethod
    def get_by_cedula(self, cedula: str) -> Optional[Socio]:
        """Obtiene un socio por su cédula."""
        pass

    @abstractmethod
    def list_all(self) -> List[Socio]:
        """Lista todos los socios."""
        pass

    @abstractmethod
    def save(self, socio: Socio) -> Socio:
        """Guarda o actualiza un socio en la BBDD."""
        pass
    
    @abstractmethod
    def get_by_usuario_id(self, usuario_id: int) -> Optional[Socio]:
        """Obtiene el socio vinculado a un ID de usuario de Django."""
        pass

# --- NUEVA INTERFAZ PARA TERRENOS (FASE 2) ---
class ITerrenoRepository(ABC):
    """
    Contrato para gestionar los puntos de suministro (Terrenos).
    """
    @abstractmethod
    def save(self, terreno: Terreno) -> Terreno:
        """Guarda o actualiza un terreno (Create/Update)."""
        pass

    @abstractmethod
    def get_by_id(self, terreno_id: int) -> Optional[Terreno]:
        """Obtiene un terreno por su ID."""
        pass

    @abstractmethod
    def list_by_socio_id(self, socio_id: int) -> List[Terreno]:
        """
        Lista todos los terrenos que pertenecen a un socio.
        Fundamental para que el socio vea sus propiedades.
        """
        pass

    @abstractmethod
    def list_by_barrio_id(self, barrio_id: int) -> List[Terreno]:
        """[NUEVO] Lista terrenos filtrados por barrio."""
        pass
    
    @abstractmethod
    def create(self, terreno: Terreno) -> Terreno:
        """
        Método explícito de creación (útil para diferenciar de updates en lógica compleja).
        """
        pass


class IMedidorRepository(ABC):
    """
    Actualizado para Fase 2: El medidor se vincula al Terreno.
    """
    @abstractmethod
    def get_by_id(self, medidor_id: int) -> Optional[Medidor]:
        pass

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> Optional[Medidor]:
        """Busca un medidor por su código único (serial)."""
        pass

    # --- CAMBIO FASE 2 ---
    @abstractmethod
    def get_by_terreno_id(self, terreno_id: int) -> Optional[Medidor]:
        """
        Obtiene el medidor instalado en un terreno específico.
        Recuerda: Un terreno tiene máximo 1 medidor activo.
        """
        pass

    @abstractmethod
    def list_all(self) -> List[Medidor]:
        pass

    @abstractmethod
    def save(self, medidor: Medidor) -> Medidor:
        pass
    
    @abstractmethod
    def create(self, medidor: Medidor) -> Medidor:
        """Creación explícita."""
        pass


class IBarrioRepository(ABC):
    @abstractmethod
    def list_all(self) -> List[Barrio]:
        pass

    @abstractmethod
    def get_by_id(self, barrio_id: int) -> Optional[Barrio]:
        pass
    
    @abstractmethod
    def get_by_nombre(self, nombre: str) -> Optional[Barrio]:
        pass

    @abstractmethod
    def save(self, barrio: Barrio) -> Barrio:
        pass
    
    @abstractmethod
    def delete(self, barrio_id: int) -> None:
        pass


class ILecturaRepository(ABC):
    @abstractmethod
    def get_latest_by_medidor(self, medidor_id: int) -> Optional[Lectura]:
        pass
    
    @abstractmethod
    def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        pass

    @abstractmethod
    def save(self, lectura: Lectura) -> Lectura:
        pass


class IFacturaRepository(ABC):
    @abstractmethod
    def get_by_id(self, factura_id: int) -> Optional[Factura]:
        pass

    @abstractmethod
    def get_by_clave_acceso(self, clave_acceso: str) -> Optional[Factura]:
        pass

    @abstractmethod
    def list_by_socio_and_date_range(
        self, socio_id: int, fecha_inicio: date, fecha_fin: date
    ) -> List[Factura]:
        pass
    
    @abstractmethod
    def list_by_socio(self, socio_id: int) -> List[Factura]:
        pass

    @abstractmethod
    def list_by_estado(self, estado: EstadoFactura) -> List[Factura]:
        pass

    @abstractmethod
    def save(self, factura: Factura) -> Factura:
        pass


class IAuthRepository(ABC):
    @abstractmethod
    def crear_usuario(self, username: str, password: str, email: str = None, rol: 'RolUsuario' = None) -> int:
        pass

    @abstractmethod
    def desactivar_usuario(self, user_id: int) -> None:
        pass

    @abstractmethod
    def activar_usuario(self, user_id: int) -> None:
        pass