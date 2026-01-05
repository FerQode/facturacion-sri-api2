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
from core.domain.terreno import Terreno
from core.shared.enums import EstadoFactura, RolUsuario

"""
Interfaces de Repositorio (Clean Architecture):
Definen los contratos estrictos que la capa de Casos de Uso utilizará.
La implementación concreta (Django ORM) estará en 'adapters/infrastructure/repositories'.
"""

class ISocioRepository(ABC):
    @abstractmethod
    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        """Obtiene un socio por su ID único."""
        pass

    @abstractmethod
    def get_by_cedula(self, cedula: str) -> Optional[Socio]:
        """Obtiene un socio por su cédula de identidad."""
        pass

    @abstractmethod
    def list_all(self) -> List[Socio]:
        """Lista todos los socios activos en el sistema."""
        pass

    @abstractmethod
    def save(self, socio: Socio) -> Socio:
        """Guarda (crea) o actualiza un socio en la base de datos."""
        pass
    
    @abstractmethod
    def get_by_usuario_id(self, usuario_id: int) -> Optional[Socio]:
        """Obtiene el perfil de socio vinculado a una cuenta de usuario (login)."""
        pass


class ITerrenoRepository(ABC):
    """
    Gestión de Puntos de Suministro (Terrenos).
    Un Socio tiene N Terrenos. Un Terreno tiene 1 Medidor.
    """
    @abstractmethod
    def save(self, terreno: Terreno) -> Terreno:
        """Persiste los cambios de un terreno."""
        pass

    @abstractmethod
    def get_by_id(self, terreno_id: int) -> Optional[Terreno]:
        """Busca un terreno por su ID."""
        pass

    @abstractmethod
    def list_by_socio_id(self, socio_id: int) -> List[Terreno]:
        """Lista todas las propiedades de un socio."""
        pass

    @abstractmethod
    def list_by_barrio_id(self, barrio_id: int) -> List[Terreno]:
        """Filtra terrenos por ubicación geográfica (Barrio)."""
        pass
    
    @abstractmethod
    def create(self, terreno: Terreno) -> Terreno:
        """Método explícito para crear un nuevo terreno."""
        pass


class IMedidorRepository(ABC):
    @abstractmethod
    def get_by_id(self, medidor_id: int) -> Optional[Medidor]:
        pass

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> Optional[Medidor]:
        """Busca por serial/código único del dispositivo."""
        pass

    @abstractmethod
    def get_by_terreno_id(self, terreno_id: int) -> Optional[Medidor]:
        """Obtiene el medidor activo instalado en un terreno."""
        pass

    @abstractmethod
    def list_all(self) -> List[Medidor]:
        pass

    @abstractmethod
    def save(self, medidor: Medidor) -> Medidor:
        pass
    
    @abstractmethod
    def create(self, medidor: Medidor) -> Medidor:
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
        """Obtiene la última lectura registrada para calcular el consumo del mes actual."""
        pass
    
    @abstractmethod
    def get_by_id(self, lectura_id: int) -> Optional[Lectura]:
        pass

    @abstractmethod
    def list_by_medidor(self, medidor_id: int, limit: int = 12) -> List[Lectura]:
        """[MEJORA] Obtiene historial de lecturas (ej: últimos 12 meses)."""
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
        """Busca una factura por la clave de acceso del SRI (49 dígitos)."""
        pass

    @abstractmethod
    def get_by_lectura_id(self, lectura_id: int) -> Optional[Factura]:
        """
        [CRÍTICO] Busca si ya existe una factura generada para una lectura específica.
        Vital para la Idempotencia (evitar duplicados).
        """
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
        """Crea o actualiza una factura y sus detalles."""
        pass


class IAuthRepository(ABC):
    @abstractmethod
    def crear_usuario(self, username: str, password: str, email: str = None, rol: 'RolUsuario' = None) -> int:
        """Crea un usuario en el sistema de identidad y retorna su ID."""
        pass

    @abstractmethod
    def desactivar_usuario(self, user_id: int) -> None:
        pass

    @abstractmethod
    def activar_usuario(self, user_id: int) -> None:
        pass