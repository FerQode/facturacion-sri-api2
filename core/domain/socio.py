# core/domain/socio.py
from dataclasses import dataclass
from typing import Optional
from datetime import date
from core.shared.enums import RolUsuario

@dataclass
class Socio:
    """
    Entidad de Dominio que representa a un socio de la junta.
    """
    # 1. CAMPOS OBLIGATORIOS
    id: Optional[int]
    cedula: str
    nombres: str
    apellidos: str
    
    # 2. CAMPOS OPCIONALES
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    # --- CAMBIO IMPORTANTE: Referencia por ID ---
    barrio_id: Optional[int] = None
    direccion: Optional[str] = None
    # --------------------------------------------

    # Datos de Sistema
    rol: Optional[RolUsuario] = RolUsuario.SOCIO
    esta_activo: bool = True
    usuario_id: Optional[int] = None 
    
    # Datos demográficos extra
    fecha_nacimiento: Optional[date] = None
    discapacidad: bool = False
    tercera_edad: bool = False

    @property
    def nombre_completo(self) -> str:
        """Helper para mostrar nombre legible"""
        return f"{self.nombres} {self.apellidos}"