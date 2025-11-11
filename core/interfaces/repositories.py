# core/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

# Importamos nuestras Entidades de Dominio
from core.domain.socio import Socio
from core.domain.medidor import Medidor
from core.domain.lectura import Lectura
from core.domain.factura import Factura
from core.domain.shared.enums import EstadoFactura

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
        [cite_start]"""Obtiene un socio por su cédula[cite: 27]."""
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
        [cite_start]"""Lista todos los medidores de un socio[cite: 9]."""
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
    def save(self, lectura: Lectura) -> Lectura:
        """Guarda una nueva lectura."""
        pass

class IFacturaRepository(ABC):
    
    @abstractmethod
    def get_by_id(self, factura_id: int) -> Optional[Factura]:
        """Obtiene una factura por su ID."""
        pass

    @abstractmethod
    def list_by_socio_and_date_range(
        self, socio_id: int, fecha_inicio: date, fecha_fin: date
    ) -> List[Factura]:
        [cite_start]"""Lista facturas de un socio en un rango de fechas[cite: 26, 35]."""
        pass

    @abstractmethod
    def list_by_estado(self, estado: EstadoFactura) -> List[Factura]:
        [cite_start]"""Lista facturas por estado (Pendiente, Pagada)[cite: 32]."""
        pass

    @abstractmethod
    def save(self, factura: Factura) -> Factura:
        """Guarda o actualiza una factura."""
        pass