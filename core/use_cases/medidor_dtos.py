# core/use_cases/medidor_dtos.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class MedidorDTO:
    """
    DTO para enviar datos de un medidor hacia afuera (Output).
    """
    id: int
    codigo: str
    socio_id: int
    esta_activo: bool
    observacion: Optional[str]
    tiene_medidor_fisico: bool

@dataclass(frozen=True)
class CrearMedidorDTO:
    """
    DTO con los datos necesarios para crear un nuevo medidor (Input).
    """
    codigo: str
    socio_id: int
    observacion: Optional[str] = None
    tiene_medidor_fisico: bool = True

@dataclass(frozen=True)
class ActualizarMedidorDTO:
    """
    DTO para actualizar un medidor existente. Todos los campos son opcionales
    para permitir actualizaciones parciales (PATCH).
    """
    codigo: Optional[str] = None
    socio_id: Optional[int] = None
    esta_activo: Optional[bool] = None
    observacion: Optional[str] = None
    tiene_medidor_fisico: Optional[bool] = None