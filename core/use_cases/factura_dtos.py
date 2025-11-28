# core/use_cases/factura_dtos.py
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class GenerarFacturaDesdeLecturaDTO:
    """
    DTO de entrada para el Caso de Uso GenerarFacturaDesdeLecturaUseCase.
    """
    lectura_id: int
    fecha_emision: date
    fecha_vencimiento: date

@dataclass(frozen=True)
class ConsultarAutorizacionDTO:
    """
    DTO para el Caso de Uso ConsultarAutorizacionUseCase.
    """
    clave_acceso: str

# --- ¡CLASE NUEVA AÑADIDA! ---
@dataclass(frozen=True)
class EnviarFacturaSRIDTO:
    """
    DTO para el Caso de Uso EnviarFacturaSRIUseCase.
    """
    factura_id: int