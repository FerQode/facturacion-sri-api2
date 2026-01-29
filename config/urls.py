# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 1. Autenticación y Seguridad (JWT)
from rest_framework_simplejwt.views import TokenRefreshView
from adapters.api.views.auth_views import CustomTokenObtainPairView

# 2. Documentación Automática (Swagger / OpenAPI)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# --- Configuración de Metadatos de la API (Swagger) ---
schema_view = get_schema_view(
   openapi.Info(
      title="API Junta de Agua 'El Arbolito' & SRI",
      default_version='v1',
      description="""
      **Sistema de Gestión de Agua y Facturación Electrónica.**
      
      **GUÍA DE AUTENTICACIÓN:**
      1. Genera tu token en `/api/v1/token/`.
      2. Copia el valor de `access`.
      3. Haz clic en el botón **Authorize** (candado gris).
      4. Escribe: `Bearer TU_TOKEN_AQUI` (respetando el espacio).
      5. Haz clic en 'Authorize' y 'Close'.
      """,
      contact=openapi.Contact(email="admin@juntaarbolito.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# --- LISTA ÚNICA DE RUTAS ---
urlpatterns = [
    # 1. Panel de Administración
    path('admin/', admin.site.urls),

    # 2. Autenticación (JWT)
    path('api/v1/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. Endpoints de Negocio (Tus Adaptadores)
    path('api/v1/', include('adapters.api.urls')),

    # 4. Documentación
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# --- CONFIGURACIÓN DE MEDIA (FOTOS) EN MODO DEBUG ---
# Esto debe ir AL FINAL para sumar las rutas estáticas a la lista urlpatterns existente.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)