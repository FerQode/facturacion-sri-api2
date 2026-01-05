# adapters/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# --- Importación de Vistas (Clean Architecture) ---
# Importamos los controladores (views) que conectan HTTP con los Casos de Uso.
from .views import (
    lectura_views,
    factura_views,
    socio_views,
    medidor_views,
    barrio_views,
    terreno_views
)

# ==============================================================================
# A. ROUTER PARA CRUDs (ViewSets)
# ==============================================================================
# El DefaultRouter crea automáticamente las rutas estándar REST:
# GET /recurso/, POST /recurso/, GET /recurso/{id}/, PUT /recurso/{id}/
router = DefaultRouter()

# 1. Gestión de Personas
router.register(r'socios', socio_views.SocioViewSet, basename='socio')

# 2. Gestión de Activos e Infraestructura
router.register(r'medidores', medidor_views.MedidorViewSet, basename='medidor')
router.register(r'barrios', barrio_views.BarrioViewSet, basename='barrio')
router.register(r'terrenos', terreno_views.TerrenoViewSet, basename='terreno')

# 3. Gestión de Lecturas (NUEVO: Incluye Historial y Registro)
# Genera:
# POST /api/v1/lecturas/ (Registrar)
# GET /api/v1/lecturas/?medidor_id=X (Historial)
router.register(r'lecturas', lectura_views.LecturaViewSet, basename='lectura')


# ==============================================================================
# B. RUTAS TRANSACCIONALES (APIViews)
# ==============================================================================
# Estas rutas ejecutan "Casos de Uso" complejos que no encajan en un CRUD simple.
# Se definen manualmente con 'path' para tener control total de la URL.

urlpatterns = [
    
    # --- Módulo de Facturación & SRI ---
    # 1. Generar: Toma una lectura, calcula montos, firma XML y envía al SRI.
    path(
        'facturas/generar/', 
        factura_views.GenerarFacturaAPIView.as_view(), 
        name='generar-factura'
    ),
    
    # 2. Reenviar: Si falló el envío automático, se reintenta por aquí.
    path(
        'facturas/enviar-sri/', 
        factura_views.EnviarFacturaSRIAPIView.as_view(), 
        name='enviar-factura-sri'
    ),
    
    # 3. Consultar: Verifica el estado de una autorización usando la clave de acceso.
    path(
        'facturas/consultar/', 
        factura_views.ConsultarAutorizacionAPIView.as_view(), 
        name='consultar-autorizacion-sri'
    ),
    
    # --- Inclusión de las Rutas Automáticas del Router ---
    # Se pone al final para que capture todas las rutas generadas arriba.
    path('', include(router.urls)),
]