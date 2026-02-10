# adapters/api/views/__init__.py

# --- CORE Billing & Finance (Existentes) ---
from .analytics_views import AnalyticsViewSet
from .barrio_views import BarrioViewSet
from .billing_views import ConsultarEstadoCuentaView, ProcesarAbonoView
from .cobro_views import CobroViewSet
from .factura_views import DescargarRideView
from .inventario_views import InventarioViewSet
from .pos_views import POSViewSet
from .usuario_views import UserProfileView

# --- Comercial (Modificado por Usuario) ---
from .comercial_views import (
    SocioViewSet, 
    FacturaViewSet, 
    PagoViewSet, 
    CatalogoRubroViewSet, 
    ProductoMaterialViewSet
)

# --- Gobernanza (Modificado por Usuario) ---
from .gobernanza_views import (
    EventoViewSet,
    SolicitudJustificacionViewSet
)

# --- MODULOS EXTRA (Safe Integration) ---
from .extra_modules_views import (
    AsistenciaViewSet,
    MultaViewSet,
    OrdenTrabajoViewSet,
    CortesViewSet,
    MedidorViewSet,
    CobroLecturaViewSet
)