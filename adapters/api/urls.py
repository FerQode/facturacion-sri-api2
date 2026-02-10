# # adapters/api/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# from adapters.api.views import (
#     # Core
#     AnalyticsViewSet, CobroViewSet, POSViewSet, UserProfileView, 
#     DescargarRideView, ConsultarEstadoCuentaView, ProcesarAbonoView,
#     # Granulares (Nativos)
#     BarrioViewSet, InventarioViewSet, LecturaViewSet, MedidorViewSet, 
#     MultaViewSet, OrdenTrabajoViewSet, CortesViewSet, SocioViewSet, TerrenoViewSet,
#     ServicioAguaViewSet,
#     # Comercial Helpers
#     FacturaViewSet, PagoViewSet, CatalogoRubroViewSet, ProductoMaterialViewSet,
#     # Gobernanza
#     EventoViewSet, SolicitudJustificacionViewSet, AsistenciaViewSet,
#     # Extras Integrados
#     CobroLecturaViewSet
# )

# router = DefaultRouter()

# # --- 1. Comercial & Clientes ---
# router.register(r'socios', SocioViewSet, basename='socio')
# router.register(r'barrios', BarrioViewSet, basename='barrio')
# router.register(r'terrenos', TerrenoViewSet, basename='terreno')
# router.register(r'rubros', CatalogoRubroViewSet, basename='rubro')

# # --- 2. Financiero & Billing ---
# router.register(r'cobros', CobroViewSet, basename='cobro')             # Ventanilla
# router.register(r'cobros-consulta', CobroLecturaViewSet, basename='cobro-consulta') # Grid Deuda
# router.register(r'facturas', FacturaViewSet, basename='factura')       # Historial
# router.register(r'pagos', PagoViewSet, basename='pago')                # Historial Pagos
# router.register(r'analytics', AnalyticsViewSet, basename='analytics')

# # --- 3. Gobernanza ---
# router.register(r'eventos', EventoViewSet, basename='evento')
# router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')
# router.register(r'multas', MultaViewSet, basename='multa')
# router.register(r'solicitudes-justificacion', SolicitudJustificacionViewSet, basename='solicitud-justificacion')

# # --- 4. Operativa ---
# router.register(r'ordenes-trabajo', OrdenTrabajoViewSet, basename='orden-trabajo')
# router.register(r'cortes', CortesViewSet, basename='corte')
# router.register(r'medidores', MedidorViewSet, basename='medidor')
# router.register(r'lecturas', LecturaViewSet, basename='lectura')
# router.register(r'servicios-agua', ServicioAguaViewSet, basename='servicio-agua')

# # --- 5. Inventario & POS ---
# router.register(r'inventario', InventarioViewSet, basename='inventario')       # POS Query
# router.register(r'materiales', ProductoMaterialViewSet, basename='material')   # CRUD Inventario
# router.register(r'pos', POSViewSet, basename='pos')                            # Venta


# urlpatterns = [
#     # Router Principal
#     path('', include(router.urls)),

#     # --- Endpoints Utilitarios ---
#     path('users/profile/', UserProfileView.as_view(), name='user-profile'),
#     path('facturas/<int:factura_id>/pdf/', DescargarRideView.as_view(), name='descargar-ride'),

#     # --- Billing System (Legacy / Específicos) ---
#     path('billing/estado-cuenta/<int:socio_id>/', ConsultarEstadoCuentaView.as_view(), name='billing-estado-cuenta'),
#     path('billing/pagar/', ProcesarAbonoView.as_view(), name='billing-pagar'),

#     # --- Documentación API ---
#     path('schema/', SpectacularAPIView.as_view(), name='schema'),
#     path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
#     path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
# ]

# adapters/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from adapters.api.views import (
    # Core
    AnalyticsViewSet, CobroViewSet, POSViewSet, UserProfileView,
    DescargarRideView, ConsultarEstadoCuentaView, ProcesarAbonoView,
    # Granulares (Nativos)
    BarrioViewSet, InventarioViewSet, LecturaViewSet, MedidorViewSet,
    MultaViewSet, OrdenTrabajoViewSet, CortesViewSet, SocioViewSet,
    # TerrenoViewSet, # Descomenta si tienes el view creado
    # ServicioAguaViewSet, # Descomenta si tienes el view creado
    # Comercial Helpers
    FacturaViewSet, PagoViewSet, CatalogoRubroViewSet, ProductoMaterialViewSet,
    # Gobernanza
    EventoViewSet, SolicitudJustificacionViewSet, AsistenciaViewSet,
    # Extras Integrados
    CobroLecturaViewSet
)

router = DefaultRouter()

# --- 1. Comercial & Clientes ---
router.register(r'socios', SocioViewSet, basename='socio')
router.register(r'barrios', BarrioViewSet, basename='barrio')
router.register(r'rubros', CatalogoRubroViewSet, basename='rubro')
# router.register(r'terrenos', TerrenoViewSet, basename='terreno') # Activar si existe el ViewSet

# --- 2. Financiero & Billing ---
router.register(r'cobros', CobroViewSet, basename='cobro')             # Ventanilla
router.register(r'cobros-consulta', CobroLecturaViewSet, basename='cobro-consulta') # Grid Deuda
router.register(r'facturas', FacturaViewSet, basename='factura')       # Historial
router.register(r'pagos', PagoViewSet, basename='pago')                # Historial Pagos
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

# ✅ LA LÍNEA MÁGICA (Traída del Código 2 para salvar el Dashboard)
router.register(r'facturas-gestion', FacturaViewSet, basename='factura-gestion')

# --- 3. Gobernanza ---
router.register(r'eventos', EventoViewSet, basename='evento')
router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')
router.register(r'multas', MultaViewSet, basename='multa')
router.register(r'solicitudes-justificacion', SolicitudJustificacionViewSet, basename='solicitud-justificacion')

# --- 4. Operativa ---
router.register(r'ordenes-trabajo', OrdenTrabajoViewSet, basename='orden-trabajo')
router.register(r'cortes', CortesViewSet, basename='corte')
router.register(r'medidores', MedidorViewSet, basename='medidor')
router.register(r'lecturas', LecturaViewSet, basename='lectura')
# router.register(r'servicios-agua', ServicioAguaViewSet, basename='servicio-agua') # Activar si existe

# --- 5. Inventario & POS ---
router.register(r'inventario', InventarioViewSet, basename='inventario')       # POS Query
router.register(r'materiales', ProductoMaterialViewSet, basename='material')   # CRUD Inventario
router.register(r'pos', POSViewSet, basename='pos')                            # Venta


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