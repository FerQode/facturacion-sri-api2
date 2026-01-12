# core/domain/multa.py
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from django.utils import timezone # Usamos timezone para ser consistentes con Django

# Importamos el Enum desde el lugar correcto
from core.shared.enums import EstadoMulta

@dataclass
class Multa:
    """
    Entidad de Dominio que representa una sanción, minga o cobro extra.
    """
    id: Optional[int]
    socio_id: int
    valor: Decimal        # ✅ Usamos 'valor' para coincidir con tus Vistas y Casos de Uso
    motivo: str
    
    # Valores por defecto
    estado: EstadoMulta = EstadoMulta.PENDIENTE
    observacion: Optional[str] = None
    fecha_creacion: datetime = field(default_factory=timezone.now)

    # --- LÓGICA DE NEGOCIO (Rich Domain Model) ---
    # Metemos la lógica aquí para que no esté dispersa en los servicios

    def anular(self, razon: str):
        """
        Anula la multa lógicamente (no la borra).
        """
        if self.estado == EstadoMulta.PAGADA:
            raise ValueError("No se puede anular una multa que ya fue PAGADA.")
        
        self.estado = EstadoMulta.ANULADA
        self.observacion = f"{self.observacion or ''} | [ANULADA]: {razon}"

    def rectificar_monto(self, nuevo_valor: Decimal, razon: str):
        """
        Corrige el valor de la multa (ej: trabajó medio día).
        """
        if self.estado == EstadoMulta.PAGADA:
            raise ValueError("No se puede rectificar una multa que ya fue PAGADA.")
        
        if nuevo_valor < 0:
            raise ValueError("El valor de la multa no puede ser negativo.")

        valor_anterior = self.valor
        self.valor = nuevo_valor
        self.observacion = f"{self.observacion or ''} | [RECTIFICADA]: ${valor_anterior} -> ${nuevo_valor}. Razón: {razon}"

    def marcar_como_pagada(self):
        """
        Finaliza el ciclo de vida de la multa.
        """
        if self.estado != EstadoMulta.PENDIENTE:
            raise ValueError(f"No se puede pagar una multa en estado {self.estado}.")
        
        self.estado = EstadoMulta.PAGADA