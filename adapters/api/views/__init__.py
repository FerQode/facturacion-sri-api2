# adapters/api/views/__init__.py

# Vistas Reales
from .analytics_views import AnalyticsViewSet
from .barrio_views import BarrioViewSet
from .billing_views import ConsultarEstadoCuentaView, ProcesarAbonoView
from .cobro_views import CobroViewSet
from .factura_views import DescargarRideView
from .inventario_views import InventarioViewSet
from .pos_views import POSViewSet
from .usuario_views import UserProfileView

# Placeholders (Stubs)
from .placeholder_views import (
    EventoViewSet,
    CortesViewSet,
    OrdenTrabajoViewSet
)