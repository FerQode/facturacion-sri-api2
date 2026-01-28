# core/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from decimal import Decimal
from core.domain.factura import Factura
from core.domain.socio import Socio
# Usamos Any para evitar imports circulares si Lectura no está disponible fácilmente
try:
    from core.domain.lectura import Lectura
except ImportError:
    Lectura = Any

try:
    from core.domain.barrio import Barrio
except ImportError:
    Barrio = Any

try:
    from core.domain.multa import Multa
except ImportError:
    Multa = Any

# --- Interfaces de Dominio ---

class IFacturaRepository(ABC):
    @abstractmethod
    def obtener_por_id(self, id: int) -> Optional[Factura]:
        """Debe retornar la entidad Factura con sus detalles y socio cargados"""
        pass

    @abstractmethod
    def existe_factura_fija_mes(self, servicio_id: int, anio: int, mes: int) -> bool:
        """Verifica si ya existe factura para un servicio fijo en ese mes/año"""
        pass

    @abstractmethod
    def guardar(self, factura: Factura) -> Factura:
        """Persiste los cambios de la factura. Retorna la factura guardada (o None)"""
        pass
    
    # Alias para compatibilidad con código legacy
    def save(self, factura: Factura) -> Any:
        return self.guardar(factura)

    @abstractmethod
    def get_by_lectura_id(self, lectura_id: int) -> Optional[Factura]:
        """Busca si existe factura generada para esa lectura (Idempotencia)"""
        pass

    @abstractmethod
    def obtener_pendientes_por_socio(self, socio_id: int) -> List[Factura]:
        """Retorna todas las facturas pendientes de un socio (Agua, Riego, Multas)"""
        pass

class IPagoRepository(ABC):
    @abstractmethod
    def obtener_sumatoria_validada(self, factura_id: int) -> float:
        pass
    
    @abstractmethod
    def tiene_pagos_pendientes(self, factura_id: int) -> bool:
        pass

    @abstractmethod
    def registrar_pagos(self, factura_id: int, pagos: List[dict]) -> None:
        pass

    @abstractmethod
    def obtener_ultimos_pagos(self, socio_id: int, limite: int = 5) -> List[Any]:
        pass

class IAuthRepository(ABC):
    @abstractmethod
    def crear_usuario(self, username: str, password: str, email: str = None, rol: Any = None) -> int:
        pass

    @abstractmethod
    def desactivar_usuario(self, user_id: int) -> None:
        pass

    @abstractmethod
    def activar_usuario(self, user_id: int) -> None:
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

class IMultaRepository(ABC):
    @abstractmethod
    def obtener_pendientes_por_socio(self, socio_id: int) -> List[Any]:
        pass

    @abstractmethod
    def get_by_id(self, multa_id: int) -> Optional[Any]: 
        pass

    @abstractmethod
    def save(self, multa: Any) -> Any:
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

class IServicioRepository(ABC):
    @abstractmethod
    def obtener_servicios_fijos_activos(self) -> List[Any]:
        pass

    @abstractmethod
    def create_automatico(self, terreno_id: int, socio_id: int, tipo: str, valor: float) -> Any:
        pass

    @abstractmethod
    def get_by_socio(self, socio_id: int) -> List[Any]:
        pass

    @abstractmethod
    def get_active_by_terreno_and_type(self, terreno_id: int, tipo: str) -> Optional[Any]:
        pass

class IMedidorRepository(ABC):
    @abstractmethod
    def get_by_id(self, medidor_id: int) -> Optional[Any]:
        pass

class ISocioRepository(ABC):
    @abstractmethod
    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        pass

    @abstractmethod
    def list_active(self) -> List[Socio]:
        pass

    @abstractmethod
    def list_by_barrio(self, barrio_id: int) -> List[Socio]:
        pass

class ITerrenoRepository(ABC):
    @abstractmethod
    def get_by_id(self, terreno_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_by_socio(self, socio_id: int) -> List[Any]:
        pass

try:
    from core.domain.evento import Evento
except ImportError:
    Evento = Any

try:
    from core.domain.asistencia import Asistencia
except ImportError:
    Asistencia = Any

class IEventoRepository(ABC):
    @abstractmethod
    def get_by_id(self, evento_id: int) -> Optional[Evento]:
        pass

    @abstractmethod
    def save(self, evento: Evento) -> Evento:
        pass
        
    @abstractmethod
    def list_all(self) -> List[Evento]:
        pass

class IAsistenciaRepository(ABC):
    @abstractmethod
    def get_by_id(self, asistencia_id: int) -> Optional[Asistencia]:
        pass

    @abstractmethod
    def get_by_evento(self, evento_id: int) -> List[Asistencia]:
        pass
        
    @abstractmethod
    def crear_masivo(self, asistencias: List[Asistencia]) -> List[Asistencia]:
        pass

    @abstractmethod
    def save(self, asistencia: Asistencia) -> Asistencia:
        pass

class IGobernanzaRepository(ABC):
    """
    Puerto para acceder a multas y gobernanza sin acoplarse a Django.
    """
    @abstractmethod
    def obtener_multas_pendientes(self, socio_id: int) -> List[Any]: # Retorna lista de Asistencias (Domain o DTO)
        pass

    @abstractmethod
    def marcar_multa_como_facturada(self, asistencia_id: int, factura_id: int) -> None:
        pass
