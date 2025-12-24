# adapters/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importamos las "Ventanillas" (Views/ViewSets)
from .views import lectura_views 
from .views import factura_views
from .views import socio_views
from .views import medidor_views
from .views import barrio_views
from .views import terreno_views  # <--- [NUEVO] Importamos la vista de Terrenos

# --- BUENA PRÁCTICA: Usar Routers para ViewSets ---
router = DefaultRouter()

# Registros CRUD
router.register(r'socios', socio_views.SocioViewSet, basename='socio')
router.register(r'medidores', medidor_views.MedidorViewSet, basename='medidor')
router.register(r'barrios', barrio_views.BarrioViewSet, basename='barrio')
router.register(r'terrenos', terreno_views.TerrenoViewSet, basename='terreno') # <--- [NUEVO] Endpoint oficial

# Estas son nuestras URLs de API.
urlpatterns = [
    # --- Rutas de Flujo Crítico (con APIView) ---
    path(
        'lecturas/registrar/', 
        lectura_views.RegistrarLecturaAPIView.as_view(), 
        name='registrar-lectura'
    ),
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
    
    # --- Rutas CRUD (manejadas por el Router) ---
    # Esto incluirá automáticamente:
    # GET /terrenos/ (Listar)
    # POST /terrenos/ (Crear con la lógica del Caso de Uso)
    # GET /terrenos/{id}/ (Detalle)
    path('', include(router.urls)),
]