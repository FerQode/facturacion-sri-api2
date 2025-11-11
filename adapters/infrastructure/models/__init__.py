# Este archivo importa los modelos para que Django los encuentre
from .socio_model import SocioModel
from .medidor_model import MedidorModel
from .lectura_model import LecturaModel
from .factura_model import FacturaModel, DetalleFacturaModel

__all__ = [
    'SocioModel', 
    'MedidorModel', 
    'LecturaModel', 
    'FacturaModel', 
    'DetalleFacturaModel'
]