# core/domain/medidor.py
from dataclasses import dataclass
from typing import Optional
from datetime import date # Necesario para la fecha de instalación

@dataclass
class Medidor:
    """
    Entidad de Dominio que representa el dispositivo físico de medición.
    
    CAMBIOS FASE 2:
    - Ya no se vincula directamente al Socio, sino a un Terreno (terreno_id).
    - Eliminamos 'tiene_medidor_fisico' porque la existencia de este objeto IMPLICA que es físico.
    - Agregamos datos técnicos como marca y lectura inicial.
    """
    id: Optional[int]
    
    # RELACIÓN CLAVE: El medidor pertenece a un punto de suministro (Terreno)
    terreno_id: Optional[int] 
    
    codigo: str           # Serial único del dispositivo
    marca: Optional[str]  # Ej: "Elster", "Sensus"
    
    lectura_inicial: float = 0.0
    
    # Estado del dispositivo: 'ACTIVO', 'INACTIVO', 'DANADO'
    # Reemplaza al antiguo booleano 'esta_activo'
    estado: str = 'ACTIVO' 
    
    observacion: Optional[str] = None
    fecha_instalacion: Optional[date] = None