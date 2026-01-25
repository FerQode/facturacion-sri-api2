# core>domain>lectura.py
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Lectura:
    """
    Entidad de Dominio: Lectura (Snapshot Inmutable).
    
    Representa el estado exacto de una medición en un momento del tiempo.
    Para cumplir con requisitos del SRI y trazabilidad, almacenamos explícitamente
    los valores utilizados para el cálculo, en lugar de recalcularlos dinámicamente.
    """
    id: Optional[int]
    medidor_id: int
    fecha: date
    
    # --- BLOQUE DE DATOS DE FACTURACIÓN (INMUTABLES) ---
    # Estos campos son obligatorios para garantizar la integridad de la factura.
    # Se deben calcular en el Caso de Uso antes de instanciar esta entidad.
    
    valor: float              # Lectura Actual
    lectura_anterior: float   # Lectura Previa (Snapshot)
    consumo_del_mes_m3: float # Resultado de la resta (Snapshot)

    # --- METADATOS Y OPCIONALES (Defaults al final) ---
    observacion: Optional[str] = None
    esta_facturada: bool = False

    # NOTA DE DISEÑO:
    # Se eliminó la @property 'consumo_calculado'. 
    # La lógica de validación (actual < anterior) y cálculo debe residir 
    # en el Caso de Uso 'RegistrarLectura' para asegurar que lo que se guarda 
    # es exactamente lo que se calculó en ese momento.