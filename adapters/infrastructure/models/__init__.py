# adapters/infrastructure/models/__init__.py

# Importamos los modelos existentes
from .socio_model import SocioModel
from .medidor_model import MedidorModel
from .lectura_model import LecturaModel
from .factura_model import FacturaModel, DetalleFacturaModel

# --- AÑADIMOS EL NUEVO MODELO DE BARRIO ---
from .barrio_model import BarrioModel

# Actualizamos la lista __all__ para exportar todo limpiamente
__all__ = [
    'SocioModel', 
    'MedidorModel', 
    'LecturaModel', 
    'FacturaModel', 
    'DetalleFacturaModel',
    'BarrioModel', # <--- Nuevo
]