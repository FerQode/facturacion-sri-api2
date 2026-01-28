from abc import ABC, abstractmethod
from typing import List, Optional, Any, Protocol, runtime_checkable, Dict
from decimal import Decimal
from core.domain.factura import Factura
from core.domain.socio import Socio
# Usamos Any para evitar imports circulares si Lectura no está disponible fácilmente
# o importamos dentro de TYPE_CHECKING
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
    
    # Alias para compatibilidad con código legacy (GenerarFacturaUseCase usa .save())
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
        """Retorna la suma de pagos (Transferencias) ya validados"""
        pass
    
    @abstractmethod
    def tiene_pagos_pendientes(self, factura_id: int) -> bool:
        """Verifica si hay pagos subidos pero no validados (Candado de Seguridad)"""
        pass

    @abstractmethod
    def registrar_pagos(self, factura_id: int, pagos: List[dict]) -> None:
        """
        Guarda nuevos pagos (Efectivo, Transferencia, etc).
        En el caso de Transferencias mixtas en caja, se asumen validadas.
        """
        pass

    @abstractmethod
    def obtener_ultimos_pagos(self, socio_id: int, limite: int = 5) -> List[Any]:
        """Retorna el historial reciente de pagos del socio via recibos"""
        pass

# ... (Existing code) ...

class ITerrenoRepository(ABC):
    @abstractmethod
    def get_by_id(self, terreno_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_by_socio(self, socio_id: int) -> List[Any]:
        """Retorna los terrenos asociados a un socio"""
        pass
    @abstractmethod
    def obtener_sumatoria_validada(self, factura_id: int) -> float:
        """Retorna la suma de pagos (Transferencias) ya validados"""
        pass
    
    @abstractmethod
    def tiene_pagos_pendientes(self, factura_id: int) -> bool:
        """Verifica si hay pagos subidos pero no validados (Candado de Seguridad)"""
        pass

    @abstractmethod
    def registrar_pagos(self, factura_id: int, pagos: List[dict]) -> None:
        """
        Guarda nuevos pagos (Efectivo, Transferencia, etc).
        En el caso de Transferencias mixtas en caja, se asumen validadas.
        """
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

# --- Interfaces Restauradas (Legacy Support) ---

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
        """Retorna lista (o QuerySet) de servicios activos de tarifa fija"""
        pass

    @abstractmethod
    def create_automatico(self, terreno_id: int, socio_id: int, tipo: str, valor: float) -> Any:
        """Crea un servicio automáticamente al registrar un terreno"""
        pass

    @abstractmethod
    def get_by_socio(self, socio_id: int) -> List[Any]:
        """Retorna los servicios asociados al socio para mapeo"""
        pass

    @abstractmethod
    def get_active_by_terreno_and_type(self, terreno_id: int, tipo: str) -> Optional[Any]:
        """Obtiene el servicio activo para un terreno y tipo específico"""
        pass

class IMedidorRepository(ABC):
    @abstractmethod
    def get_by_id(self, medidor_id: int) -> Optional[Any]:
        pass

class ISocioRepository(ABC):
    @abstractmethod
    @abstractmethod
    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        pass

    @abstractmethod
    def list_active(self) -> List[Socio]:
        """Listar todos los socios activos"""
        pass

    @abstractmethod
    def list_by_barrio(self, barrio_id: int) -> List[Socio]:
        """Listar socios activos de un barrio"""
        pass

class ITerrenoRepository(ABC):
    @abstractmethod
    def get_by_id(self, terreno_id: int) -> Optional[Any]:
        pass



try:
    from core.domain.evento import Evento, TipoEvento, EstadoEvento
except ImportError:
    Evento = Any

try:
    from core.domain.asistencia import Asistencia, EstadoJustificacion
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
        """Insert masivo para optimizar"""
        pass

    @abstractmethod
    def save(self, asistencia: Asistencia) -> Asistencia:
        pass
