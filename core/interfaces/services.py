# core/interfaces/services.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# Importamos la Entidad de Dominio
from core.domain.factura import Factura

"""
Interfaces de Servicios Externos:
Definen los contratos para conectarse con APIs o servicios
fuera de nuestro sistema (como el SRI, envío de emails, etc.)
"""

# --- Estructuras de Datos para el SRI ---

@dataclass(frozen=True)
class SRIAuthData:
    """
    Contiene los "secretos" para la autenticación con el SRI.
    (Estos datos vendrán de tu settings.py o variables de entorno).
    """
    firma_path: str
    firma_pass: str
    sri_url_recepcion: str
    sri_url_autorizacion: str

@dataclass(frozen=True)
class SRIResponse:
    """
    Una respuesta estandarizada del servicio del SRI.
    Oculta la complejidad del XML de respuesta del SRI.
    """
    exito: bool
    autorizacion_id: Optional[str] # El ID de autorización (claveAcceso)
    estado: str # Ej: "AUTORIZADO", "DEVUELTA", "EN PROCESO"
    mensaje_error: Optional[str]
    xml_enviado: str
    xml_respuesta: Optional[str]


# --- Interfaz del Servicio SRI ---

class ISRIService(ABC):
    """
    Contrato que define cómo nuestro sistema interactúa con el SRI.
    """
    
    @abstractmethod
    def __init__(self, auth: SRIAuthData):
        """
        La implementación de este servicio DEBE recibir 
        las credenciales de autenticación.
        """
        pass

    @abstractmethod
    def enviar_factura(self, factura: Factura) -> SRIResponse:
        """
        Toma una entidad Factura de nuestro dominio, la convierte
        a XML, la firma digitalmente, la envía al SRI y devuelve
        una respuesta estandarizada.
        
        Este método es una "Fachada" (Facade): oculta toda
        la complejidad de (1) Generar XML, (2) Firmar, (3) Enviar SOAP/REST.
        """
        pass

    @abstractmethod
    def consultar_autorizacion(self, clave_acceso: str) -> SRIResponse:
        """
        Consulta el estado de una factura ya enviada usando su claveAcceso.
        """
        pass

# --- Interfaz de Notificaciones (Opcional pero recomendado) ---

class INotificationService(ABC):
    """
    [cite_start]Contrato para enviar notificaciones (ej: email al socio [cite: 42]).
    """
    
    @abstractmethod
    def enviar_notificacion_factura(self, email_socio: str, factura: Factura):
        pass