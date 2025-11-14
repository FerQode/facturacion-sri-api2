from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importamos las "Ventanillas" (Views/ViewSets)
from .views import lectura_views 
from .views import factura_views
from .views import socio_views # <--- ¡NUEVA IMPORTACIÓN!

# --- BUENA PRÁCTICA: Usar Routers para ViewSets ---
# 1. Creamos un router
router = DefaultRouter()

# 2. Registramos nuestro ViewSet.
#    DRF generará automáticamente:
#    - GET /socios/ (para list)
#    - POST /socios/ (para create)
#    - GET /socios/<pk>/ (para retrieve)
#    - PUT /socios/<pk>/ (para update)
#    - PATCH /socios/<pk>/ (para partial_update)
#    - DELETE /socios/<pk>/ (para destroy)
router.register(r'socios', socio_views.SocioViewSet, basename='socio')


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
    
    # --- Rutas CRUD (manejadas por el Router) ---
    # Incluimos las URLs generadas por el router
    path('', include(router.urls)),
]