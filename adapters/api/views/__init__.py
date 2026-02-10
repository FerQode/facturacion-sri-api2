# adapters/api/views/__init__.py

# --- CORE Billing & Finance ---
from .analytics_views import AnalyticsViewSet
from .billing_views import ConsultarEstadoCuentaView, ProcesarAbonoView
from .cobro_views import CobroViewSet, CobroLecturaViewSet # ✅ CobroLecturaView integrada en cobro_views
from .factura_views import DescargarRideView
from .pos_views import POSViewSet
from .usuario_views import UserProfileView

# --- Vistas Granulares (Nativas y Robustas) ---
from .barrio_views import BarrioViewSet
from .inventario_views import InventarioViewSet         # ReadOnly (POS)
from .lectura_views import LecturaViewSet               # Gestión de Lecturas
from .medidor_views import MedidorViewSet               # Gestión de Medidores
from .multa_views import MultaViewSet                   # Gestión de Multas (Archivo Propio)
from .servicio_views import OrdenTrabajoViewSet, CortesViewSet # Gestión Operativa
from .socio_views import SocioViewSet                   # Gestión de Socios
from .terreno_views import TerrenoViewSet               # Gestión de Terrenos
from .servicio_agua_views import ServicioAguaViewSet    # CRUD Servicios Base

# --- Comercial Helpers ---
from .comercial_views import (
    FacturaViewSet,          # ReadOnly List
    PagoViewSet,             # CRUD Pagos
    CatalogoRubroViewSet,    # Catálogo
    ProductoMaterialViewSet  # CRUD Materiales
)

# --- Gobernanza ---
from .gobernanza_views import (
    EventoViewSet,
    SolicitudJustificacionViewSet,
    AsistenciaViewSet        # ✅ AsistenciaViewSet integrada en gobernanza_views
)