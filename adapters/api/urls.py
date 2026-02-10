from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from adapters.api.views import (
    # Core/Legacy
    AnalyticsViewSet, BarrioViewSet, CobroViewSet, InventarioViewSet, POSViewSet,
    UserProfileView, DescargarRideView, ConsultarEstadoCuentaView, ProcesarAbonoView,
    # Comercial
    SocioViewSet, FacturaViewSet, PagoViewSet, CatalogoRubroViewSet, ProductoMaterialViewSet,
    # Gobernanza
    EventoViewSet, SolicitudJustificacionViewSet,
    # Extra Modules
    AsistenciaViewSet, MultaViewSet, OrdenTrabajoViewSet, CortesViewSet, MedidorViewSet, CobroLecturaViewSet
)

router = DefaultRouter()

# --- 1. Comercial & Clientes ---
router.register(r'socios', SocioViewSet, basename='socio')
router.register(r'barrios', BarrioViewSet, basename='barrio')
router.register(r'rubros', CatalogoRubroViewSet, basename='rubro')

# --- 2. Financiero & Billing ---
# CobroViewSet es complejo (Acciones). CobroLectura es para listar deudas.
router.register(r'cobros', CobroViewSet, basename='cobro') 
router.register(r'cobros-consulta', CobroLecturaViewSet, basename='cobro-consulta')
router.register(r'facturas', FacturaViewSet, basename='factura') # Solo lectura segun comercial_views
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

# --- 3. Gobernanza ---
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')
router.register(r'multas', MultaViewSet, basename='multa')
router.register(r'solicitudes-justificacion', SolicitudJustificacionViewSet, basename='solicitud-justificacion')

# --- 4. Operativa ---
router.register(r'ordenes-trabajo', OrdenTrabajoViewSet, basename='orden-trabajo')
router.register(r'cortes', CortesViewSet, basename='corte')
router.register(r'medidores', MedidorViewSet, basename='medidor')

# --- 5. Inventario & POS ---
router.register(r'inventario', InventarioViewSet, basename='inventario')
router.register(r'materiales', ProductoMaterialViewSet, basename='material') # Alias si se requiere
router.register(r'pos', POSViewSet, basename='pos')


urlpatterns = [
    # Router Principal
    path('', include(router.urls)),

    # --- Endpoints Utilitarios ---
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('facturas/<int:factura_id>/pdf/', DescargarRideView.as_view(), name='descargar-ride'),

    # --- Billing System (Legacy / Específicos) ---
    path('billing/estado-cuenta/<int:socio_id>/', ConsultarEstadoCuentaView.as_view(), name='billing-estado-cuenta'),
    path('billing/pagar/', ProcesarAbonoView.as_view(), name='billing-pagar'),

    # --- Documentación API ---
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
