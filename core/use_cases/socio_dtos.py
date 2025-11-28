# core/use_cases/socio_dtos.py
from dataclasses import dataclass
from typing import Optional
from core.shared.enums import RolUsuario

# DTO para la respuesta (lo que enviamos al exterior)
@dataclass(frozen=True)
class SocioDTO:
    id: int
    cedula: str
    nombres: str
    apellidos: str
    email: Optional[str]
    telefono: Optional[str]
    barrio: str
    rol: str # Enviamos el valor simple (string)
    esta_activo: bool

# DTO de entrada para crear un socio
@dataclass(frozen=True)
class CrearSocioDTO:
    cedula: str
    nombres: str
    apellidos: str
    barrio: str
    rol: RolUsuario # Usamos el Enum para la lógica interna
    email: Optional[str] = None
    telefono: Optional[str] = None
    # --- NUEVOS CAMPOS ---
    username: Optional[str] = None # Opcional, si no viene usamos la cédula
    password: Optional[str] = None # Opcional, si no viene generamos una

# DTO de entrada para actualizar (todos los campos opcionales)
@dataclass(frozen=True)
class ActualizarSocioDTO:
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    barrio: Optional[str] = None
    rol: Optional[RolUsuario] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    esta_activo: Optional[bool] = None