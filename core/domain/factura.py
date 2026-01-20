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

    # --- LÓGICA DE NEGOCIO (CORREGIDA) ---

    def calcular_total_con_medidor(self, consumo_m3: int):
        self.detalles.clear()

        if consumo_m3 <= TARIFA_BASE_M3:
            # CASO A: Consumo dentro de la base (Tarifa Plana)
            # Se cobra 1 unidad de servicio, independientemente del volumen exacto
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Servicio de Agua Potable (Base hasta {TARIFA_BASE_M3} m³)",
                cantidad=Decimal(1),
                precio_unitario=TARIFA_BASE_PRECIO,
                subtotal=TARIFA_BASE_PRECIO
            ))
            self.subtotal = TARIFA_BASE_PRECIO
        else:
            # CASO B: Consumo Excedente
            consumo_excedente = consumo_m3 - TARIFA_BASE_M3

            # 1. Cobro la base completa como 1 unidad
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Servicio Base ({TARIFA_BASE_M3} m³)",
                cantidad=Decimal(1),
                precio_unitario=TARIFA_BASE_PRECIO,
                subtotal=TARIFA_BASE_PRECIO
            ))

            # 2. Cobro el excedente por metro cúbico
            subtotal_excedente = Decimal(consumo_excedente) * TARIFA_EXCEDENTE_PRECIO
            self.detalles.append(DetalleFactura(
                id=None,
                concepto=f"Consumo Excedente ({consumo_excedente} m³)",
                cantidad=Decimal(consumo_excedente),
                precio_unitario=TARIFA_EXCEDENTE_PRECIO,
                subtotal=subtotal_excedente
            ))

            self.subtotal = TARIFA_BASE_PRECIO + subtotal_excedente

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