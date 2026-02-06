# adapters/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# --- Importación de Vistas (Clean Architecture) ---
from .views import (
    lectura_views,
    multa_views,
    factura_views # Contiene: Generar, Masiva, Cobros, SRI, DescargarRide
)
from .views.factura_views import DescargarRideView
    servicio_agua_views, # ✅ AGREGADO: Importamos la vista del Servicio de Agua
    cobro_views,
    sri_views, # ✅ AGREGADO: Vista para sincronización SRI
    gobernanza_views, # ✅ AGREGADO: Módulo de Gobernanza
    analytics_views, # ✅ AGREGADO: Reportes y KPIs (Fase 4)
    usuario_views # ✅ AGREGADO: Perfil de usuario
)

# ==============================================================================
# A. ROUTER PARA CRUDs y VIEWSETS (Rutas Automáticas)
# ==============================================================================
router = DefaultRouter()

# 1. Gestión de Personas
router.register(r'socios', socio_views.SocioViewSet, basename='socio')

# 2. Gestión de Activos e Infraestructura
router.register(r'medidores', medidor_views.MedidorViewSet, basename='medidor')
router.register(r'barrios', barrio_views.BarrioViewSet, basename='barrio')
router.register(r'terrenos', terreno_views.TerrenoViewSet, basename='terreno')

# ✅ NUEVO: Gestión de Servicios de Agua (Tarifa Fija)
# Esto habilita: POST /api/v1/servicios-agua/
router.register(r'servicios-agua', servicio_agua_views.ServicioAguaViewSet, basename='servicios-agua')

# ✅ NUEVO: Gestión de Gobernanza (Eventos y Asistencia)
router.register(r'eventos', gobernanza_views.EventoViewSet, basename='eventos')

# 3. Gestión de Lecturas e Historial
router.register(r'lecturas', lectura_views.LecturaViewSet, basename='lectura')

# 4. Gestión de Multas (Impugnaciones y Rectificaciones)
# Genera: PATCH /api/v1/multas/{id}/impugnar/
router.register(r'multas', multa_views.MultaViewSet, basename='multa')

# 5. Facturación Masiva y Pre-visualización
# Genera rutas automáticas para las @actions definidas:
# GET /api/v1/facturas-gestion/pendientes/ (Tabla de revisión)
# POST /api/v1/facturas-gestion/emision-masiva/ (Ejecutar masivo)
router.register(r'facturas-gestion', factura_views.FacturaMasivaViewSet, basename='facturas-gestion')

# 6. Cobros y Pagos (Caja)
# Genera: POST /api/v1/cobros/registrar/
router.register(r'cobros', cobro_views.CobroViewSet, basename='cobros')

# 7. SRI (Sincronización y Reintentos)
# Genera: POST /api/v1/sri/{pk}/sincronizar/
router.register(r'sri', sri_views.SRIViewSet, basename='sri')

# 8. Reportes Inteligentes (Fase 4)
# Genera: GET /api/v1/analytics/dashboard-kpis/
router.register(r'analytics', analytics_views.AnalyticsViewSet, basename='analytics')


# ==============================================================================
# B. RUTAS MANUALES (APIViews - Transaccionales)
# ==============================================================================

urlpatterns = [
    
    # --- PERFIL DEL USUARIO LOGUEADO ---
    path(
        'usuarios/me/', 
        usuario_views.UserProfileView.as_view(), 
        name='user-profile'
    ),

    # --- Módulo de Facturación Individual & SRI ---
    # Endpoint transaccional para crear UNA factura específica desde lectura
    path(
        'facturas/generar/',
        factura_views.GenerarFacturaAPIView.as_view(),
        name='generar-factura'
    ),

    # ✅ NUEVO: Generación Masiva para Tarifa Fija
    path(
        'facturas/generar-fijas/',
        factura_views.GenerarFacturasFijasAPIView.as_view(),
        name='generar-facturas-fijas'
    ),
    # Reintento manual de envío al SRI
    path(
        'facturas/enviar-sri/',
        factura_views.EnviarFacturaSRIAPIView.as_view(),
        name='enviar-factura-sri'
    ),

    # Consulta de estado de documento
    path(
        'facturas/consultar/',
        factura_views.ConsultarAutorizacionAPIView.as_view(),
        factura_views.ConsultarAutorizacionAPIView.as_view(),
        name='consultar-autorizacion-sri'
    ),

    # Descarga de RIDE (PDF)
    path(
        'facturas/<int:factura_id>/pdf/',
        DescargarRideView.as_view(),
        name='descargar-ride'
    ),

    # App Móvil (Historial del Socio)
    path(
        'mis-facturas/',
        factura_views.MisFacturasAPIView.as_view(),
        name='mis-facturas'
    ),

    # --- Inclusión de las Rutas Automáticas del Router ---
    path('', include(router.urls)),
]