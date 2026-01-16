# core/use_cases/lectura_dtos.py
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass(frozen=True)
class RegistrarLecturaDTO:
    """
    Data Transfer Object para mover datos desde la API hacia el Caso de Uso.
    Es inmutable (frozen=True) para garantizar la integridad de los datos.
    """
    medidor_id: int
    
    # ✅ Usamos 'lectura_actual' para coincidir con el Serializer y el Frontend
    lectura_actual: float
    
    fecha_lectura: date
    operador_id: int
    observacion: Optional[str] = None