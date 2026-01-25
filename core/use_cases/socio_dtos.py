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
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    email: Optional[str]
    telefono: Optional[str]
    
    # --- UBICACIÓN ---
    barrio_id: Optional[int]    # ID para preseleccionar dropdown en frontend
    direccion: Optional[str]    # Dirección específica
    # -----------------
    
    rol: str 
    esta_activo: bool
    
    # ✅ NUEVO CAMPO (Soluciona el TypeError)
    # Permite al frontend saber qué ID de usuario (login) tiene asociado este socio
    usuario_id: Optional[int] = None 

# =============================================================================
# 2. DTO DE ENTRADA (Creación)
# =============================================================================
@dataclass(frozen=True)
class CrearSocioDTO:
    identificacion: str
    tipo_identificacion: str
    nombres: str
    apellidos: str
    
    # --- UBICACIÓN ---
    barrio_id: int      # Obligatorio
    direccion: str      # Obligatorio
    # -----------------
    
    rol: RolUsuario 
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    # Credenciales opcionales (si no se envían, se usa la cédula)
    username: Optional[str] = None 
    password: Optional[str] = None 

# =============================================================================
# 3. DTO DE ENTRADA (Actualización)
# =============================================================================
@dataclass(frozen=True)
class ActualizarSocioDTO:
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    
    # --- UBICACIÓN ---
    barrio_id: Optional[int] = None
    direccion: Optional[str] = None
    # -----------------
    
    rol: Optional[RolUsuario] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    esta_activo: Optional[bool] = None