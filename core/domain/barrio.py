# core/domain/barrio.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Barrio:
    """
    Entidad que representa un Barrio o sector geográfico de la Junta.
    Es una entidad raíz, pero también actúa como un catálogo.
    """
    id: Optional[int]
    nombre: str
    descripcion: Optional[str] = None
    
    # Podríamos añadir un campo 'activo' para soft-delete si lo deseas en el futuro
    activo: bool = True