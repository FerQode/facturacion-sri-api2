# core/domain/asistencia.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class EstadoJustificacion(str, Enum):
    SIN_SOLICITUD = "SIN_SOLICITUD"
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"

class EstadoAsistencia(str, Enum):
    PENDIENTE = "PENDIENTE"
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"
    JUSTIFICADO = "JUSTIFICADO"

@dataclass
class Asistencia:
    id: Optional[int]
    evento_id: int
    socio_id: int
    estado: EstadoAsistencia = EstadoAsistencia.PENDIENTE
    estado_justificacion: EstadoJustificacion = EstadoJustificacion.SIN_SOLICITUD
    multa_factura_id: Optional[int] = None
    observacion: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def marcar_asistencia(self):
        self.estado = EstadoAsistencia.PRESENTE
        
    def solicitar_justificacion(self, motivo: str):
        self.estado_justificacion = EstadoJustificacion.PENDIENTE
        self.observacion = motivo
