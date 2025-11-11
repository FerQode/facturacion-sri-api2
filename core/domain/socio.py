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
    email: Optional[str]
    telefono: Optional[str]
    barrio: str
    rol: RolUsuario = RolUsuario.SOCIO
    esta_activo: bool = True
    
    # Un socio puede tener múltiples medidores (líneas de servicio)
    # Usamos 'List[int]' (IDs) para mantenerlo simple y desacoplado.
    medidores_ids: List[int] = field(default_factory=list)

    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"
    
    def anadir_medidor(self, medidor_id: int):
        if medidor_id not in self.medidores_ids:
            self.medidores_ids.append(medidor_id)