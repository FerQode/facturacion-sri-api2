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
    identificacion: str
    tipo_identificacion: str
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

    # Flag para controlar validación (útil para hidratación desde BD con data histórica sucia)
    from dataclasses import InitVar
    _validate: InitVar[bool] = True

    @property
    def nombre_completo(self) -> str:
        """Helper para mostrar nombre legible"""
        return f"{self.nombres} {self.apellidos}"

    def __post_init__(self, _validate):
        """
        Validación de Dominio Puro:
        Asegura que la identificación sea matemáticamente válida según el algoritmo del SRI.
        """
        if not _validate:
            return

        # Solo validamos si tenemos el dato (al crear/actualizar)
        if self.identificacion and self.tipo_identificacion:
            try:
                # Importación diferida para no ensuciar el namespace global si no se usa
                from stdnum.ec import ci as validador_cedula # 'ci' = Cédula de Identidad
                from stdnum.ec import ruc as validador_ruc
                
                tipo = str(self.tipo_identificacion).upper()
                
                if 'CEDULA' in tipo or tipo == 'C':
                    validador_cedula.validate(self.identificacion)
                
                elif 'RUC' in tipo or tipo == 'R':
                    validador_ruc.validate(self.identificacion)
                    
                # Pasaporte no tiene algoritmo estándar público riguroso más allá de longitud
                elif 'PASAPORTE' in tipo or tipo == 'P':
                    if len(self.identificacion) < 5:
                        raise ValueError("El pasaporte debe tener al menos 5 caracteres.")

            except Exception as e:
                # Re-lanzamos como ValueError para que sea capturado por capas superiores
                # Los validadores de stdnum lanzan InvalidChecksum, InvalidLength, etc.
                raise ValueError(f"Identificación inválida ({self.tipo_identificacion}): {str(e)}")