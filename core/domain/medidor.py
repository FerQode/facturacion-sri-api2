# core/domain/medidor.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Medidor:
    """
    Entidad que representa una línea de servicio o medidor de agua.
    Un socio puede tener uno o varios.
    """
    id: Optional[int]
    codigo: str  # El número/código del medidor
    socio_id: int # El ID del Socio dueño
    esta_activo: bool = True
    observacion: Optional[str] = None # Para medidores antiguos/inactivos
    
    # Si no tiene medidor físico, el cobro es fijo
    tiene_medidor_fisico: bool = True