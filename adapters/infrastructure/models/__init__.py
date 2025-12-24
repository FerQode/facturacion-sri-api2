# adapters/infrastructure/models/__init__.py

# 1. Importamos los modelos existentes
from .socio_model import SocioModel
from .medidor_model import MedidorModel
from .lectura_model import LecturaModel
# Nota: DetalleFacturaModel viene de factura_model, lo mantenemos así
from .factura_model import FacturaModel, DetalleFacturaModel 
from .barrio_model import BarrioModel

# 2. --- AÑADIMOS EL NUEVO MODELO DE TERRENO ---
from .terreno_model import TerrenoModel

# 3. Actualizamos la lista __all__ para exportar todo limpiamente
__all__ = [
    'SocioModel', 
    'MedidorModel', 
    'LecturaModel', 
    'FacturaModel', 
    'DetalleFacturaModel',
    'BarrioModel',
    'TerrenoModel', # <--- ¡Esto es lo que faltaba para solucionar el error!
]