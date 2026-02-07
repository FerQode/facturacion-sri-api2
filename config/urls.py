# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 1. Autenticación y Seguridad (JWT)
from rest_framework_simplejwt.views import TokenRefreshView
from adapters.api.views.auth_views import CustomTokenObtainPairView

# 2. Documentación Automática (OpenAPI 3.0 - drf-spectacular)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# --- LISTA ÚNICA DE RUTAS (ESTÁNDAR v5.1) ---
urlpatterns = [
    # 1. Panel de Administración
    path('admin/', admin.site.urls),

    # 2. Autenticación (JWT)
    path('api/v1/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. Endpoints de Negocio (Tus Adaptadores)
    path('api/v1/', include('adapters.api.urls')),

    # 4. Documentación Moderna (OpenAPI 3) - TODAS BAJO /api/
    # Schema (YAML/JSON)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI (Renombrado de /swagger/ a /api/docs/)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Redoc (Documentación Cliente - Renombrado de /redoc/ a /api/redoc/)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# --- CONFIGURACIÓN DE MEDIA (FOTOS) EN MODO DEBUG ---
# Esto debe ir AL FINAL para sumar las rutas estáticas a la lista urlpatterns existente.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)