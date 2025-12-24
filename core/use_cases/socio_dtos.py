# core/use_cases/socio_dtos.py
from dataclasses import dataclass
from typing import Optional
from core.shared.enums import RolUsuario

# =============================================================================
# 1. DTO DE SALIDA (Respuesta al Frontend)
# =============================================================================
@dataclass(frozen=True)
class SocioDTO:
    id: int
    cedula: str
    nombres: str
    apellidos: str
    email: Optional[str]
    telefono: Optional[str]
    
    # --- ACTUALIZADO FASE 3/4 ---
    # Antes: barrio: str
    barrio_id: Optional[int]    # Devolvemos el ID para que el frontend preseleccione el dropdown
    direccion: Optional[str]    # La dirección específica (calle, lote, etc.)
    # ----------------------------
    
    rol: str 
    esta_activo: bool

# =============================================================================
# 2. DTO DE ENTRADA (Creación)
# =============================================================================
@dataclass(frozen=True)
class CrearSocioDTO:
    cedula: str
    nombres: str
    apellidos: str
    
    # --- ACTUALIZADO ---
    barrio_id: int      # El Frontend debe enviar el ID del barrio seleccionado
    direccion: str      # Obligatorio para una junta de agua
    # -------------------
    
    rol: RolUsuario 
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    # Credenciales opcionales
    username: Optional[str] = None 
    password: Optional[str] = None 

# =============================================================================
# 3. DTO DE ENTRADA (Actualización)
# =============================================================================
@dataclass(frozen=True)
class ActualizarSocioDTO:
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    
    # --- ACTUALIZADO ---
    barrio_id: Optional[int] = None
    direccion: Optional[str] = None
    # -------------------
    
    rol: Optional[RolUsuario] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    esta_activo: Optional[bool] = None