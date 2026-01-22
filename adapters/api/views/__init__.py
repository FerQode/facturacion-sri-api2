# Este archivo expone las vistas para que puedan ser importadas fácilmente
from .lectura_views import LecturaViewSet
from .factura_views import (
    FacturaMasivaViewSet, 
    GenerarFacturaAPIView, 
    GenerarFacturasFijasAPIView,
    CobroViewSet,
    EnviarFacturaSRIAPIView, 
    ConsultarAutorizacionAPIView,
    MisFacturasAPIView
)
from .socio_views import SocioViewSet
from .sri_views import SRIViewSet
from .medidor_views import MedidorViewSet
from .barrio_views import BarrioViewSet
from .terreno_views import TerrenoViewSet
from .multa_views import MultaViewSet
from .servicio_agua_views import ServicioAguaViewSet # ✅ Aquí conectamos lo nuevo