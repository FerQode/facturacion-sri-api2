# core/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

# Importamos nuestras Entidades de Dominio
from core.domain.socio import Socio
from core.domain.medidor import Medidor
from core.domain.lectura import Lectura
from core.domain.factura import Factura
from core.shared.enums import EstadoFactura, RolUsuario # Asegúrate de importar RolUsuario si se usa

"""
Interfaces de Repositorio:
Definen los contratos que la capa de Casos de Uso (Use Cases)
utilizará para interactuar con la base de datos, sin saber
qué base de datos es (gracias a la Inversión de Dependencia).
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

class IMedidorRepository(ABC):

    @abstractmethod
    def get_by_id(self, medidor_id: int) -> Optional[Medidor]:
        """Obtiene un medidor por su ID."""
        pass

    @abstractmethod
    def list_by_socio(self, socio_id: int) -> List[Medidor]:
        """Lista todos los medidores de un socio."""
        pass

    @abstractmethod
    def save(self, medidor: Medidor) -> Medidor:
        """Guarda o actualiza un medidor."""
        pass

class ILecturaRepository(ABC):
    
    @abstractmethod
    def get_latest_by_medidor(self, medidor_id: int) -> Optional[Lectura]:
        """Obtiene la última lectura registrada para un medidor."""
        pass

    @abstractmethod
    def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        "..."
        pass

    @abstractmethod
    def save(self, lectura: Lectura) -> Lectura:
        """Guarda una nueva lectura."""
        pass

class IFacturaRepository(ABC):
    
    @abstractmethod
    def get_by_id(self, factura_id: int) -> Optional[Factura]:
        """Obtiene una factura por su ID."""
        pass

    # --- MÉTODO NUEVO A AÑADIR ---
    @abstractmethod
    def get_by_clave_acceso(self, clave_acceso: str) -> Optional[Factura]:
        """Obtiene una factura por su clave de acceso del SRI."""
        pass
    # ----------------------------

    @abstractmethod
    def list_by_socio_and_date_range(
        self, socio_id: int, fecha_inicio: date, fecha_fin: date
    ) -> List[Factura]:
        """Lista facturas de un socio en un rango de fechas."""
        pass

    @abstractmethod
    def list_by_estado(self, estado: EstadoFactura) -> List[Factura]:
        """Lista facturas por estado (Pendiente, Pagada)."""
        pass

    @abstractmethod
    def save(self, factura: Factura) -> Factura:
        """Guarda o actualiza una factura."""
        pass

# --- INTERFAZ ACTULIZADA ---
class IAuthRepository(ABC):
    @abstractmethod
    def crear_usuario(self, username: str, password: str, email: str = None, rol: 'RolUsuario' = None) -> int:
        "Crea un uduario y devuelve su ID"
        pass

    @abstractmethod
    def desactivar_usuario(self, user_id: int) -> None:
        "Desactiva un usuario (Soft Delete)"
        pass

    @abstractmethod
    def activar_usuario(self, user_id: int) -> None:
        "Reactivar un usurario previamente desactivado"
        pass

