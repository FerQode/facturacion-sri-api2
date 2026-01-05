# config/urls.py

"""
Configuración Central de URLs del Proyecto.
Define los puntos de entrada principales: Admin, Auth, API y Documentación.
"""
from django.contrib import admin
from django.urls import path, include

# 1. Autenticación y Seguridad (JWT)
from rest_framework_simplejwt.views import TokenRefreshView
from adapters.api.views.auth_views import CustomTokenObtainPairView

# 2. Documentación Automática (Swagger / OpenAPI)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# --- Configuración de Metadatos de la API (Swagger) ---
# Esto genera la página web que describe tu API automáticamente.
schema_view = get_schema_view(
   openapi.Info(
      title="API Junta de Agua 'El Arbolito' & SRI",
      default_version='v1',
      description=(
          "Documentación técnica de los endpoints del Sistema de Gestión de Agua "
          "y Facturación Electrónica con validación SRI."
      ),
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="admin@juntaarbolito.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   # En desarrollo (DEBUG=True) permitimos ver esto sin login.
   # En producción, podrías restringirlo.
   permission_classes=(permissions.AllowAny,), 
)

urlpatterns = [
    # --- 1. Panel de Administración de Django ---
    # Interfaz gráfica por defecto para gestionar la BBDD
    path('admin/', admin.site.urls),
    
    # --- 2. Autenticación y Seguridad (JWT) ---
    # Login: Recibe usuario/pass -> Devuelve Access Token + Refresh Token
    path('api/v1/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Refresh: Recibe Refresh Token -> Devuelve nuevo Access Token (para no loguearse a cada rato)
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # --- 3. Endpoints de Negocio (Tus Adaptadores) ---
    # Aquí incluimos todas las rutas definidas en tu aplicación 'adapters'.
    # El prefijo 'api/v1/' es estándar para versionar tu API.
    path('api/v1/', include('adapters.api.urls')),

    # --- 4. Documentación Interactiva ---
    # Swagger UI: La interfaz azul clásica para probar endpoints visualmente
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # Redoc: Una interfaz más moderna y limpia para leer la documentación
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]