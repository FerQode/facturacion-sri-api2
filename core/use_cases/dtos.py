# core/use_cases/dtos.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

"""
Data Transfer Objects (DTOs):
Son estructuras de datos simples (sin lógica) que usamos
para pasar información HASTA y DESDE los Casos de Uso.
"""

# =============================================================================
# 1. DTOs para Lectura
# =============================================================================
@dataclass(frozen=True)
class RegistrarLecturaDTO:
    medidor_id: int
    # CORRECCIÓN: Cambiado de int a Decimal para aceptar valores como 250.50
    lectura_actual_m3: Decimal 
    fecha_lectura: date
    operador_id: int 
    observacion: Optional[str] = None

# =============================================================================
# 2. DTOs para Facturación (NUEVO - Agregado para solucionar el error)
# =============================================================================
@dataclass(frozen=True)
class GenerarFacturaDesdeLecturaDTO:
    """
    Datos necesarios para transformar una Lectura en una Factura.
    """
    lectura_id: int
    fecha_emision: str      # Usamos str para recibir fechas 'YYYY-MM-DD' directas del JSON
    fecha_vencimiento: str

# =============================================================================
# 3. DTOs para Pago
# =============================================================================
@dataclass(frozen=True)
class RegistrarPagoDTO:
    factura_id: int
    fecha_pago: date
    monto_pagado: Decimal
    tesorero_id: int