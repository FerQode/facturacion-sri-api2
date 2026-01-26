from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal
from datetime import date

@dataclass
class DeudaDTO:
    factura_id: int
    periodo: str # "Enero 2026"
    detalle: str
    valor: Decimal
    consumo_m3: Optional[int] = None
    archivo_xml: Optional[str] = None
    archivo_pdf: Optional[str] = None

@dataclass
class PropiedadDTO:
    id: int
    direccion: str
    tipo_servicio: str # "MEDIDO" o "FIJO"
    medidor: Optional[str]
    deudas: List[DeudaDTO] = field(default_factory=list)

@dataclass
class ObligacionGeneralDTO:
    factura_id: int
    tipo: str # "MULTA", "OTROS"
    concepto: str
    fecha_evento: Optional[date]
    valor: Decimal

@dataclass
class PagoHistorialDTO:
    fecha: date
    monto: Decimal
    recibo_nro: str
    archivo_pdf: Optional[str] = None # Si hubiera recibo PDF

@dataclass
class ResumenFinancieroDTO:
    total_deuda: Decimal
    cantidad_facturas_pendientes: int

@dataclass
class SocioResumenDTO:
    nombres: str
    identificacion: str
    email: str

@dataclass
class EstadoCuentaDTO:
    socio: SocioResumenDTO
    resumen_financiero: ResumenFinancieroDTO
    propiedades: List[PropiedadDTO] = field(default_factory=list)
    obligaciones_generales: List[ObligacionGeneralDTO] = field(default_factory=list)
    historial_pagos_recientes: List[PagoHistorialDTO] = field(default_factory=list)
