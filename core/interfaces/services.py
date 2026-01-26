from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.domain.factura import Factura
from core.domain.socio import Socio

@dataclass
class SRIAuthData:
    firma_path: str
    firma_pass: str
    sri_url_recepcion: str
    sri_url_autorizacion: str

@dataclass
class SRIResponse:
    exito: bool
    autorizacion_id: Optional[str]
    estado: str
    mensaje_error: Optional[str]
    xml_enviado: Optional[str]
    xml_enviado: Optional[str]
    xml_respuesta: Optional[Dict[str, Any]]

class ISRIService(ABC):
    @abstractmethod
    def generar_clave_acceso(self, fecha_emision: Any, nro_factura: str) -> str:
        """Genera la clave de acceso de 49 dígitos para el SRI (Usa RUC configurado)"""
        pass

    @abstractmethod
    def enviar_factura(self, factura: Factura, socio: Socio) -> SRIResponse:
        """Intenta enviar y autorizar la factura en el SRI"""
        pass

    @abstractmethod
    def consultar_autorizacion(self, clave_acceso: str) -> SRIResponse:
        """Consulta el estado de una autorización por clave de acceso"""
        pass

class IEmailService(ABC):
    @abstractmethod
    def enviar_notificacion_factura(self, email_destinatario: str, nombre_socio: str, numero_factura: int, xml_autorizado: str) -> bool:
        """Envía el correo con el XML adjunto"""
        pass

    @abstractmethod
    def enviar_notificacion_multa(self, email_destinatario: str, nombre_socio: str, evento_nombre: str, valor_multa: float) -> bool:
        """Envía notificación de multa por inasistencia"""
        pass
