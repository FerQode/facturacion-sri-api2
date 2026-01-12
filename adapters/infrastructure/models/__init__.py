# adapters/infrastructure/models/__init__.py

# 1. Modelos Base (Existentes)
from .socio_model import SocioModel
from .barrio_model import BarrioModel
from .terreno_model import TerrenoModel
from .medidor_model import MedidorModel

# 2. Modelos de Operación
from .lectura_model import LecturaModel
from .factura_model import FacturaModel, DetalleFacturaModel

# 3. --- NUEVOS MODELOS (Multas y Pagos Mixtos) ---
# Estos son los que faltaban y causaban el error de importación
from .multa_model import MultaModel
from .pago_model import PagoModel

# 4. Actualizamos la lista __all__ para exportar todo limpiamente
__all__ = [
    'SocioModel', 
    'BarrioModel',
    'TerrenoModel',
    'MedidorModel', 
    'LecturaModel', 
    'FacturaModel', 
    'DetalleFacturaModel',
    'MultaModel',   # ✅ Agregado
    'PagoModel',    # ✅ Agregado
]