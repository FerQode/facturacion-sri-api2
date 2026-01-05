# core>uses_cases>medidor_dtos.py
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# 1. DTOs de SALIDA (Lo que enviamos al Frontend)
# =============================================================================

@dataclass(frozen=True)
class MedidorDTO:
    """
    DTO para enviar datos de un medidor hacia afuera (Output).
    Actualizado para reflejar la relación con Terreno y datos técnicos.
    """
    id: int
    terreno_id: Optional[int] # Ahora se vincula al Terreno (o None si está en bodega)
    codigo: str
    marca: Optional[str]
    lectura_inicial: float
    estado: str               # 'ACTIVO', 'INACTIVO', 'DANADO', etc.
    observacion: Optional[str]
    fecha_instalacion: Optional[str] = None # Opcional, como string ISO

# =============================================================================
# 2. DTOs de ENTRADA (Lo que recibimos del Frontend)
# =============================================================================

@dataclass(frozen=True)
class RegistrarMedidorDTO:
    """
    DTO para crear un medidor nuevo (generalmente usado al crear el Terreno).
    """
    terreno_id: int
    codigo: str
    marca: Optional[str] = None
    lectura_inicial: float = 0.0
    observacion: Optional[str] = None

@dataclass(frozen=True)
class ActualizarMedidorDTO:
    """
    DTO para CORREGIR datos de un medidor existente (PATCH).
    OJO: Esto NO es para cambiar el medidor físico, solo para corregir
    errores de digitación (ej: marca mal escrita).
    """
    codigo: Optional[str] = None
    marca: Optional[str] = None
    observacion: Optional[str] = None
    # No permitimos cambiar 'lectura_inicial' ni 'estado' aquí a la ligera
    # para proteger la integridad contable.

# =============================================================================
# 3. DTO ESPECÍFICO PARA PROCESO DE NEGOCIO (Reemplazo)
# =============================================================================

@dataclass(frozen=True)
class ReemplazarMedidorDTO:
    """
    DTO Especializado para el Caso de Uso 'ReemplazarMedidor'.
    Contiene la información necesaria para cerrar el ciclo del viejo
    y abrir el del nuevo.
    """
    # Contexto
    terreno_id: int
    usuario_id: int  # CRÍTICO: ID del usuario que realiza el cambio (Auditoría)

    # Datos para cerrar el Medidor Viejo
    lectura_final_viejo: float
    motivo_cambio: str # Ej: 'DANADO', 'ROBADO', 'VIDA_UTIL'

    # Datos para abrir el Medidor Nuevo
    codigo_nuevo: str
    marca_nueva: str
    lectura_inicial_nuevo: float = 0.0