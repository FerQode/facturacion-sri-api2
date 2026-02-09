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
from .pago_model import PagoModel, DetallePagoModel
from .servicio_model import ServicioModel
from .gobernanza_models import EventoModel, AsistenciaModel, SolicitudJustificacionModel
from .sri_models import SRISecuencialModel
from .catalogo_models import CatalogoRubroModel
from .cuenta_por_cobrar_model import CuentaPorCobrarModel
from .orden_trabajo_model import OrdenTrabajoModel
from .evidencia_orden_model import EvidenciaOrdenTrabajoModel
from .inventario_models import ProductoMaterial

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
    'DetallePagoModel',
    'ServicioModel',
    'EventoModel', 
    'AsistenciaModel',
    'SolicitudJustificacionModel',
    'SRISecuencialModel',
    'CatalogoRubroModel',
    'CuentaPorCobrarModel',
    'OrdenTrabajoModel',
    'EvidenciaOrdenTrabajoModel',
    'ProductoMaterial',
]