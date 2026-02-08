# core/domain/factura.py
from dataclasses import dataclass, field
from datetime import date, datetime
from django.utils import timezone
from decimal import Decimal
from typing import Optional, List
from core.shared.enums import EstadoFactura
from core.domain.lectura import Lectura

# --- CONSTANTES DE NEGOCIO ---
TARIFA_BASE_M3: int = 120
TARIFA_BASE_PRECIO: Decimal = Decimal("3.00")
TARIFA_EXCEDENTE_PRECIO: Decimal = Decimal("0.25")
TARIFA_FIJA_SIN_MEDIDOR: Decimal = Decimal("5.00")

@dataclass
class DetalleFactura:
    id: Optional[int]
    concepto: str
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal

@dataclass
class Factura:
    """
    Entidad de Dominio que representa la factura y sus datos tributarios.
    """
    id: Optional[int]
    socio_id: int
    medidor_id: Optional[int]
    fecha_emision: date
    fecha_vencimiento: date
    
    # Periodo Fiscal
    anio: int = 2025
    mes: int = 1
    
    servicio_id: Optional[int] = None # Added for Tarifa Fija (Moved here to avoid default arg error)

    # Campos automáticos
    fecha_registro: datetime = field(default_factory=timezone.now)

    estado: EstadoFactura = EstadoFactura.PENDIENTE
    lectura: Optional[Lectura] = None

    detalles: List[DetalleFactura] = field(default_factory=list)
    subtotal: Decimal = Decimal("0.00")
    impuestos: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")

    # --- CAMPOS SRI ---
    sri_ambiente: int = 1  # 1: Pruebas, 2: Producción
    sri_tipo_emision: int = 1 # 1: Normal
    sri_clave_acceso: Optional[str] = None
    sri_fecha_autorizacion: Optional[datetime] = None
    sri_xml_autorizado: Optional[str] = None
    sri_mensaje_error: Optional[str] = None
    estado_sri: Optional[str] = None
    
    # Archivos adjuntos (Rutas/URLs)
    archivo_pdf: Optional[str] = None
    archivo_xml_path: Optional[str] = None

    # --- LÓGICA DE NEGOCIO (CORREGIDA) ---

    def calcular_total_con_medidor(self, 
            consumo_m3: int, 
            # Parámetros dinámicos desde el Servicio/Contrato
            tarifa_base_m3: int = 15,
            tarifa_base_precio: Decimal = Decimal("3.00"),
            tarifa_excedente_precio: Decimal = Decimal("0.25")
        ):
        self.detalles.clear()

        # CASO A: Consumo dentro de la base
        if consumo_m3 <= tarifa_base_m3:
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Servicio de Agua Potable (Base hasta {tarifa_base_m3} m³)",
                cantidad=Decimal(1),
                precio_unitario=tarifa_base_precio,
                subtotal=tarifa_base_precio
            ))
            self.subtotal = tarifa_base_precio
        
        # CASO B: Consumo Excedente
        else:
            consumo_excedente = consumo_m3 - tarifa_base_m3

            # 1. Base
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Servicio Base ({tarifa_base_m3} m³)",
                cantidad=Decimal(1),
                precio_unitario=tarifa_base_precio,
                subtotal=tarifa_base_precio
            ))

            # 2. Excedente
            subtotal_excedente = Decimal(consumo_excedente) * tarifa_excedente_precio
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Consumo Excedente ({consumo_excedente} m³ a ${tarifa_excedente_precio}/m³)",
                cantidad=Decimal(consumo_excedente),
                precio_unitario=tarifa_excedente_precio,
                subtotal=subtotal_excedente
            ))

            self.subtotal = tarifa_base_precio + subtotal_excedente

        self.total = self.subtotal + self.impuestos

    def calcular_total_sin_medidor(self):
        self.detalles.clear()
        self.detalles.append(DetalleFactura(
            id=None,
            concepto="Tarifa fija mensual sin medidor",
            cantidad=Decimal(1),
            precio_unitario=TARIFA_FIJA_SIN_MEDIDOR,
            subtotal=TARIFA_FIJA_SIN_MEDIDOR
        ))
        self.subtotal = TARIFA_FIJA_SIN_MEDIDOR
        self.total = self.subtotal + self.impuestos

    def agregar_multa(self, concepto: str, valor: Decimal):
        """
        Método para inyectar multas desde el Servicio de Facturación.
        """
        self.detalles.append(DetalleFactura(
            id=None,
            concepto=f"MULTA: {concepto}",
            cantidad=Decimal(1),
            precio_unitario=valor,
            subtotal=valor
        ))
        self.subtotal += valor
        self.total = self.subtotal + self.impuestos

    def marcar_como_pagada(self):
        if self.estado == EstadoFactura.PENDIENTE:
            self.estado = EstadoFactura.PAGADA
        else:
            raise ValueError("Solo se puede pagar una factura pendiente.")