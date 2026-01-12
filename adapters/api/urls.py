# adapters/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# --- Importación de Vistas (Clean Architecture) ---
from .views import (
    lectura_views,
    factura_views, # Aquí están las clases nuevas (FacturaMasivaViewSet, CobroViewSet)
    socio_views,
    medidor_views,
    barrio_views,
    terreno_views
)

# ==============================================================================
# A. ROUTER PARA CRUDs y VIEWSETS
# ==============================================================================
router = DefaultRouter()

# 1. Gestión de Personas
router.register(r'socios', socio_views.SocioViewSet, basename='socio')

# 2. Gestión de Activos e Infraestructura
router.register(r'medidores', medidor_views.MedidorViewSet, basename='medidor')
router.register(r'barrios', barrio_views.BarrioViewSet, basename='barrio')
router.register(r'terrenos', terreno_views.TerrenoViewSet, basename='terreno')

# 3. Gestión de Lecturas
router.register(r'lecturas', lectura_views.LecturaViewSet, basename='lectura')

# 4. ✅ NUEVO: Facturación Masiva y Pre-visualización
# Genera rutas automáticas para las @actions definidas:
# GET /api/v1/facturas-gestion/pendientes/ (Pre-visualización)
# POST /api/v1/facturas-gestion/emision-masiva/ (Generar)
router.register(r'facturas-gestion', factura_views.FacturaMasivaViewSet, basename='facturas-gestion')

# 5. ✅ NUEVO: Cobros y Pagos
# Genera: POST /api/v1/cobros/registrar/
router.register(r'cobros', factura_views.CobroViewSet, basename='cobros')


# ==============================================================================
# B. RUTAS MANUALES (APIViews)
# ==============================================================================

urlpatterns = [
    
    # --- Módulo de Facturación Individual & SRI ---
    path(
        'facturas/generar/', 
        factura_views.GenerarFacturaAPIView.as_view(), 
        name='generar-factura'
    ),
    
    path(
        'facturas/enviar-sri/', 
        factura_views.EnviarFacturaSRIAPIView.as_view(), 
        name='enviar-factura-sri'
    ),
    
    path(
        'facturas/consultar/', 
        factura_views.ConsultarAutorizacionAPIView.as_view(), 
        name='consultar-autorizacion-sri'
    ),

    # App Móvil (Historial)
    path(
        'mis-facturas/',
        factura_views.MisFacturasAPIView.as_view(),
        name='mis-facturas'
    ),
    
    # --- Inclusión de las Rutas Automáticas del Router ---
    path('', include(router.urls)),
]