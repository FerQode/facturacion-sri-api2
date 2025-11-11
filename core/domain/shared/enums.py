# core/domain/shared/enums.py
from enum import Enum

class EstadoFactura(Enum):
    """
    Representa el estado de una factura.
    """
    [cite_start]PENDIENTE = "Pendiente"  # Factura sin pago [cite: 31]
    [cite_start]PAGADA = "Pagada"      # Factura pagada [cite: 30]
    ANULADA = "Anulada"

class RolUsuario(Enum):
    """
    [cite_start]Roles del sistema. [cite: 42]
    """
    ADMINISTRADOR = "Administrador"
    TESORERO = "Tesorero"
    OPERADOR = "Operador"
    SOCIO = "Socio"