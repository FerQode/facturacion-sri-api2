# core/domain/shared/enums.py
from enum import Enum

class EstadoFactura(Enum):
    """
    Representa el estado de una factura.
    """
    PENDIENTE = "Pendiente"  # Factura sin pago
    PAGADA = "Pagada"      # Factura pagada
    ANULADA = "Anulada"

class RolUsuario(Enum):
    """
    Roles del sistema.
    """
    ADMINISTRADOR = "Administrador"
    TESORERO = "Tesorero"
    OPERADOR = "Operador"
    SOCIO = "Socio"