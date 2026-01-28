# core/domain/evento.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from enum import Enum

class TipoEvento(str, Enum):
    MINGA = "MINGA"
    SESION = "SESION"
    APORTE = "APORTE"

class EstadoEvento(str, Enum):
    PROGRAMADA = "PROGRAMADA"
    BORRADOR = "BORRADOR"
    FINALIZADO = "FINALIZADO"

@dataclass
class Evento:
    id: Optional[int]
    nombre: str
    tipo: TipoEvento
    fecha: date
    valor_multa: float
    estado: EstadoEvento = EstadoEvento.PROGRAMADA
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def cerrar_evento(self):
        if self.estado == EstadoEvento.FINALIZADO:
            raise ValueError("El evento ya está finalizado")
        self.estado = EstadoEvento.FINALIZADO
