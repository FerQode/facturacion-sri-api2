# core/domain/shared/enums.py
from enum import Enum

class EstadoFactura(Enum):
    """
    Representa el estado de una factura.
    """
    PENDIENTE = 'PENDIENTE'
    POR_VALIDAR = 'POR_VALIDAR'
    PAGADA = 'PAGADA'
    ANULADA = 'ANULADA'

class RolUsuario(Enum):
    """
    Roles del sistema.
    """
    ADMINISTRADOR = "ADMINISTRADOR"
    TESORERO = "TESORERO"
    OPERADOR = "OPERADOR"
    SOCIO = "SOCIO"

class MetodoPagoEnum(Enum):
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"

class CodigoSRIEnum(Enum):
    # Tabla 24 del SRI (Formas de Pago)
    SIN_UTILIZACION_SISTEMA_FINANCIERO = "01" # Efectivo
    OTROS_CON_UTILIZACION_SISTEMA_FINANCIERO = "20" # Transferencias

class EstadoMulta(Enum):
    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"