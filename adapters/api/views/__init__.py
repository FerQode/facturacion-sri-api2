# adapters/api/views/__init__.py

# Este archivo expone las vistas para que puedan ser importadas fácilmente
from .comercial_views import (
    SocioViewSet, 
    FacturaViewSet, 
    PagoViewSet, 
    CatalogoRubroViewSet, 
    ProductoMaterialViewSet
)

from .lectura_views import LecturaViewSet
from .factura_views import DescargarRideView
from .sri_views import SRIViewSet
from .medidor_views import MedidorViewSet
from .barrio_views import BarrioViewSet
from .terreno_views import TerrenoViewSet
from .multa_views import MultaViewSet
from .servicio_agua_views import ServicioAguaViewSet
from .gobernanza_views import EventoViewSet
from .analytics_views import AnalyticsViewSet
from .usuario_views import UserProfileView
from .cobro_views import CobroViewSet