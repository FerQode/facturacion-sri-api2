# core/domain/socio.py
from dataclasses import dataclass, field
from typing import List, Optional
from core.shared.enums import RolUsuario

@dataclass
class Socio:
    """
    Entidad que representa a un socio de la junta de riego.
    """
    id: Optional[int]
    cedula: str
    nombres: str
    apellidos: str
    barrio: str
    
    # --- CAMPOS OPCIONALES (Con valor por defecto) ---
    # Deben ir DESPUÉS de los campos obligatorios para evitar el TypeError
    
    email: Optional[str] = None
    telefono: Optional[str] = None
    rol: RolUsuario = RolUsuario.SOCIO
    esta_activo: bool = True
    
    # Vinculación con el sistema de autenticación (ID del User de Django)
    usuario_id: Optional[int] = None 
    
    # Un socio puede tener múltiples medidores (líneas de servicio)
    medidores_ids: List[int] = field(default_factory=list)

    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"
    
    def anadir_medidor(self, medidor_id: int):
        if medidor_id not in self.medidores_ids:
            self.medidores_ids.append(medidor_id)