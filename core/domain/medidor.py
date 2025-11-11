# core/domain/medidor.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Medidor:
    """
    Entidad que representa una línea de servicio o medidor de agua.
    [cite_start]Un socio puede tener uno o varios. [cite: 9]
    """
    id: Optional[int]
    codigo: str  # El número/código del medidor
    socio_id: int # El ID del Socio dueño
    esta_activo: bool = True
    [cite_start]observacion: Optional[str] = None # Para medidores antiguos/inactivos [cite: 5]
    
    # [cite_start]Si no tiene medidor físico, el cobro es fijo [cite: 8]
    tiene_medidor_fisico: bool = True