from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# Importamos todo desde el __init__.py centralizado
from adapters.api.views import (
    AnalyticsViewSet,
    BarrioViewSet,
    CobroViewSet,
    InventarioViewSet,
    POSViewSet,
    EventoViewSet,
    CortesViewSet,
    OrdenTrabajoViewSet,
    UserProfileView,
    DescargarRideView,
    ConsultarEstadoCuentaView,
    ProcesarAbonoView
)

router = DefaultRouter()

# 1. Rutas Reales (Core)
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
router.register(r'barrios', BarrioViewSet, basename='barrio')
router.register(r'cobros', CobroViewSet, basename='cobro')
router.register(r'inventario', InventarioViewSet, basename='inventario')
router.register(r'pos', POSViewSet, basename='pos')

# 2. Rutas Placeholder (Faltantes pero requeridas por Frontend)
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'cortes', CortesViewSet, basename='corte')
router.register(r'ordenes-trabajo', OrdenTrabajoViewSet, basename='orden-trabajo')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),

    # Endpoints Sueltos (APIViews)
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('facturas/<int:factura_id>/pdf/', DescargarRideView.as_view(), name='descargar-ride'),
    
    # Billing (Rutas Legacy/Específicas)
    path('billing/estado-cuenta/<int:socio_id>/', ConsultarEstadoCuentaView.as_view(), name='billing-estado-cuenta'),
    path('billing/pagar/', ProcesarAbonoView.as_view(), name='billing-pagar'),

    # Documentación API
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
