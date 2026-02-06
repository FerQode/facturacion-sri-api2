# adapters/infrastructure/models/__init__.py

# 1. Modelos Base (Existentes)
from .socio_model import SocioModel
from .barrio_model import BarrioModel
from .terreno_model import TerrenoModel
from .medidor_model import MedidorModel

# 2. Modelos de Operación
from .lectura_model import LecturaModel
from .factura_model import FacturaModel, DetalleFacturaModel

# 3. --- NUEVOS MODELOS (Multas, Pagos y Servicios) ---
from .multa_model import MultaModel
from .pago_model import PagoModel
# ✅ AQUI ESTABA EL ERROR: Faltaba esta línea
from .servicio_model import ServicioModel
from .evento_models import EventoModel, AsistenciaModel # ✅ NUEVO FASE 2 
from .sri_models import SRISecuencialModel # ✅ NUEVO FASE 3

# 4. Actualizamos la lista __all__ para exportar todo limpiamente
__all__ = [
    'SocioModel', 
    'BarrioModel',
    'TerrenoModel',
    'MedidorModel', 
    'LecturaModel', 
    'FacturaModel', 
    'DetalleFacturaModel',
    'MultaModel',
    'PagoModel',
    'ServicioModel',
    'EventoModel', 
    'AsistenciaModel',
    'SRISecuencialModel',
]