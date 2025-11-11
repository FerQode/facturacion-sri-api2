# core/domain/factura.py
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal # Usar Decimal para dinero, NUNCA float
from typing import Optional, List
from core.shared.enums import EstadoFactura
from core.domain.lectura import Lectura

# Definimos las constantes de negocio basadas en los requisitos
TARIFA_BASE_M3: int = 120
TARIFA_BASE_PRECIO: Decimal = Decimal("3.00")
TARIFA_EXCEDENTE_PRECIO: Decimal = Decimal("0.50")
TARIFA_FIJA_SIN_MEDIDOR: Decimal = Decimal("5.00")

@dataclass
class DetalleFactura:
    """
    Una línea de ítem dentro de la factura (ej: Consumo base, Excedente)
    """
    id: Optional[int]
    concepto: str
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal

@dataclass
class Factura:
    """
    Entidad que representa la factura mensual de un socio.
    """
    id: Optional[int]
    socio_id: int
    medidor_id: Optional[int] # Opcional, por si es socio sin medidor
    fecha_emision: date
    fecha_vencimiento: date
    estado: EstadoFactura = EstadoFactura.PENDIENTE
    
    lectura: Optional[Lectura] = None # La lectura que genera esta factura
    
    detalles: List[DetalleFactura] = field(default_factory=list)
    subtotal: Decimal = Decimal("0.00")
    impuestos: Decimal = Decimal("0.00") # (IVA 0% para agua de riego)
    total: Decimal = Decimal("0.00")

    # --- LÓGICA DE NEGOCIO ---
    
    def calcular_total_con_medidor(self, consumo_m3: int):
        """
        Calcula el total de la factura para un socio CON medidor.
        Esta es lógica de negocio pura.
        """
        self.detalles.clear()
        
        if consumo_m3 <= TARIFA_BASE_M3:
            # Solo paga la base
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Consumo base hasta {TARIFA_BASE_M3} m³",
                cantidad=Decimal(consumo_m3),
                precio_unitario=TARIFA_BASE_PRECIO / TARIFA_BASE_M3,
                subtotal=TARIFA_BASE_PRECIO
            ))
            self.subtotal = TARIFA_BASE_PRECIO
        
        else:
            # Paga la base + excedente
            consumo_excedente = consumo_m3 - TARIFA_BASE_M3
            
            # 1. Detalle de la base
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Consumo base ({TARIFA_BASE_M3} m³)",
                cantidad=Decimal(TARIFA_BASE_M3),
                precio_unitario=TARIFA_BASE_PRECIO / TARIFA_BASE_M3,
                subtotal=TARIFA_BASE_PRECIO
            ))
            
            # 2. Detalle del excedente
            subtotal_excedente = Decimal(consumo_excedente) * TARIFA_EXCEDENTE_PRECIO
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Consumo excedente ({consumo_excedente} m³)",
                cantidad=Decimal(consumo_excedente),
                precio_unitario=TARIFA_EXCEDENTE_PRECIO,
                subtotal=subtotal_excedente
            ))
            
            self.subtotal = TARIFA_BASE_PRECIO + subtotal_excedente

        self.total = self.subtotal + self.impuestos # Actualiza el total

    def calcular_total_sin_medidor(self):
        """
        Calcula el total para un socio SIN medidor (tarifa fija).
        """
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

    def marcar_como_pagada(self):
        """
        Actualiza el estado de la factura.
        """
        if self.estado == EstadoFactura.PENDIENTE:
            self.estado = EstadoFactura.PAGADA
        else:
            raise ValueError("Solo se puede pagar una factura pendiente.")