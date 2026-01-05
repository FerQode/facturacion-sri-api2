# core>domain>terreno.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Terreno:
    id: Optional[int]
    socio_id: int
    barrio_id: int
    direccion: str
    es_cometida_activa: bool
    # Campos opcionales para cuando leemos datos (no para escribir)
    nombre_barrio: Optional[str] = None
    created_at: Optional[datetime] = None