# core/domain/lectura.py

from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Lectura:
    """
    Entidad que representa el registro de consumo (toma de datos) de un medidor.
    Actualizado para Fase 4 (Soporte de decimales y cambio de medidor).
    """
    id: Optional[int]
    medidor_id: int
    
    # Usamos 'valor' para estandarizar con el Repositorio y el Modelo
    valor: float 
    
    fecha: date
    
    # Campos opcionales (Defaults van al final)
    observacion: Optional[str] = None
    esta_facturada: bool = False
    
    # Campo auxiliar para cálculos (no siempre se guarda en BD en la misma fila)
    lectura_anterior: Optional[float] = None 

    @property
    def consumo_calculado(self) -> float:
        """
        Calcula el consumo del período si existe una lectura anterior.
        """
        if self.lectura_anterior is None:
            return 0.0
            
        if self.valor < self.lectura_anterior:
            # Aquí podríamos manejar la lógica de "vuelta al contador" (reset)
            # Por ahora, mantenemos la validación estricta
            raise ValueError(f"Inconsistencia: Lectura actual ({self.valor}) menor a anterior ({self.lectura_anterior}).")
        
        # Redondeamos a 2 decimales para evitar problemas de coma flotante
        return round(self.valor - self.lectura_anterior, 2)