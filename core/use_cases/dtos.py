# core/use_cases/dtos.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

"""
Data Transfer Objects (DTOs):
Son estructuras de datos simples (sin lógica) que usamos
para pasar información HASTA y DESDE los Casos de Uso.
Esto evita que los Casos de Uso dependan de, por ejemplo,
un Serializer de DRF o un request HTTP.
"""

# --- DTOs para Lectura ---
@dataclass(frozen=True)
class RegistrarLecturaDTO:
    medidor_id: int
    lectura_actual_m3: int
    fecha_lectura: date
    operador_id: int # Para auditoría


# --- DTOs para Pago ---
@dataclass(frozen=True)
class RegistrarPagoDTO:
    factura_id: int
    fecha_pago: date
    monto_pagado: Decimal
    tesorero_id: int # Para auditoría