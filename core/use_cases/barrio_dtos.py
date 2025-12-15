# core/use_cases/barrio_dtos.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class BarrioDTO:
    """
    DTO de Salida. Representa los datos de un barrio que enviamos al exterior via API.
    """
    id: int
    nombre: str
    descripcion: Optional[str]
    activo: bool

@dataclass(frozen=True)
class CrearBarrioDTO:
    """
    DTO de Entrada para crear.
    Solo pedimos los datos necesarios para registrar un nuevo barrio.
    """
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True

@dataclass(frozen=True)
class ActualizarBarrioDTO:
    """
    DTO de Entrada para actualizar.
    Todos los campos son opcionales para permitir actualizaciones parciales (PATCH).
    """
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None