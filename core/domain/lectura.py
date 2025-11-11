# core/domain/lectura.py
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Lectura:
    """
    Entidad que representa el registro de consumo de un medidor.
    """
    id: Optional[int]
    medidor_id: int
    fecha_lectura: date
    lectura_actual_m3: int # Valor actual en metros cúbicos
    lectura_anterior_m3: int # Valor con el que se facturó el mes pasado
    
    @property
    def consumo_del_mes_m3(self) -> int:
        """
        Calcula el consumo del período.
        """
        if self.lectura_actual_m3 < self.lectura_anterior_m3:
            # Manejo de reinicio del medidor (caso anómalo)
            # Aquí iría lógica más compleja, pero por ahora lanzamos error
            raise ValueError("Lectura actual no puede ser menor a la anterior.")
        
        return self.lectura_actual_m3 - self.lectura_anterior_m3