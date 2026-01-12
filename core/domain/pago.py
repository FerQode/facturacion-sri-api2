# core/domain/pago.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal
from core.shared.enums import MetodoPagoEnum

@dataclass
class Pago:
    id: Optional[int]
    factura_id: int
    metodo: MetodoPagoEnum
    monto: Decimal
    referencia: Optional[str] = None # Para el # de comprobante Pichincha
    fecha: datetime = datetime.now()
    observacion: Optional[str] = None # Ej: "Socio envió captura por WhatsApp"