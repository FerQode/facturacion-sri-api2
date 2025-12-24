from dataclasses import dataclass
from typing import Optional

@dataclass
class RegistrarTerrenoDTO:
    """
    Data Transfer Object: Define estrictamente qué datos debe enviar
    el Frontend/API para registrar un terreno.
    """
    socio_id: int
    barrio_id: int
    direccion: str
    
    # Decisión de negocio: ¿Instalamos medidor o es solo derecho de agua?
    tiene_medidor: bool
    
    # Datos opcionales (Solo obligatorios si tiene_medidor = True)
    codigo_medidor: Optional[str] = None
    marca_medidor: Optional[str] = None
    lectura_inicial: Optional[float] = 0.0
    observacion: Optional[str] = None