# core/domain/socio.py

from dataclasses import dataclass
from typing import Optional
from datetime import date
from core.shared.enums import RolUsuario

@dataclass
class Socio:
    """
    Entidad de Dominio que representa a un socio de la junta.
    Actualizada para Fase 3 y 4 (Infraestructura y API).
    """
    # 1. CAMPOS OBLIGATORIOS (Sin valor por defecto)
    id: Optional[int]
    cedula: str
    nombres: str
    apellidos: str
    
    # 2. CAMPOS OPCIONALES (Con valor por defecto = None o un valor fijo)
    # NOTA: En Python dataclasses, los campos con defaults deben ir AL FINAL.
    
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    # --- CORRECCIÓN CRÍTICA: Campos nuevos que envía el Repositorio ---
    # Reemplazamos 'barrio: str' por 'barrio_id' y agregamos 'direccion'
    barrio_id: Optional[int] = None
    direccion: Optional[str] = None
    # ------------------------------------------------------------------

    # Datos de Sistema
    rol: Optional[RolUsuario] = RolUsuario.SOCIO
    esta_activo: bool = True
    usuario_id: Optional[int] = None 
    
    # Datos demográficos extra (opcionales)
    fecha_nacimiento: Optional[date] = None
    discapacidad: bool = False
    tercera_edad: bool = False

    def nombre_completo(self) -> str:
        """Helper para mostrar nombre legible"""
        return f"{self.nombres} {self.apellidos}"
    
    # NOTA: Eliminamos 'medidores_ids' y 'anadir_medidor'.
    # Razón: En la nueva arquitectura, la relación es Socio <- Terreno <- Medidor.
    # No necesitamos guardar una lista de IDs aquí manualmante.