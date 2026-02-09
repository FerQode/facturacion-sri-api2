# adapters/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from adapters.api.views import (
    SocioViewSet, 
    FacturaViewSet, 
    PagoViewSet,
    CatalogoRubroViewSet,
    ProductoMaterialViewSet,
    ProcesarAbonoView,
    ProcesarAbonoView,
    ConsultarEstadoCuentaView,
    EventoViewSet,
    CortesViewSet,
    OrdenTrabajoViewSet,
    POSViewSet,
    InventarioViewSet,
    BarrioViewSet
)

router = DefaultRouter()
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'barrios', BarrioViewSet, basename='barrio')
router.register(r'socios', SocioViewSet, basename='socio')
router.register(r'facturas', FacturaViewSet, basename='factura')
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'rubros', CatalogoRubroViewSet, basename='rubro')
# router.register(r'inventario', ProductoMaterialViewSet, basename='inventario') # Original inventario route
# Fase 3
router.register(r'cortes', CortesViewSet, basename='cortes')
router.register(r'ordenes-trabajo', OrdenTrabajoViewSet, basename='ordenes-trabajo')

# Fase 4 - POS & Inventario
router.register(r'pos', POSViewSet, basename='pos')
router.register(r'inventario', InventarioViewSet, basename='inventario')

urlpatterns = [
    path('', include(router.urls)),
    path('billing/pagar/', ProcesarAbonoView.as_view(), name='procesar-abono'),
    path('billing/estado-cuenta/<int:socio_id>/', ConsultarEstadoCuentaView.as_view(), name='consultar-estado-cuenta'),
]

