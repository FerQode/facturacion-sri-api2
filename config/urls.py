# config/urls.py

"""
Configuración de URLs del Proyecto.
"""
from django.contrib import admin
from django.urls import path, include

# 1. Imports para Autenticación (JWT)
from rest_framework_simplejwt.views import TokenRefreshView
# Importamos tu vista personalizada de login
from adapters.api.views.auth_views import CustomTokenObtainPairView

# 2. Imports para Documentación (Swagger / Drf-yasg)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# --- Configuración de Metadatos de la API (Swagger) ---
schema_view = get_schema_view(
   openapi.Info(
      title="API Facturación SRI y Agua Potable",
      default_version='v1',
      description="Documentación técnica de los endpoints del Sistema de Gestión de Agua y Facturación Electrónica.",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="admin@juntaagua.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,), # Permite ver la doc sin estar logueado (ideal para desarrollo)
)

urlpatterns = [
    # --- 1. Panel de Administración de Django ---
    path('admin/', admin.site.urls),
    
    # --- 2. Autenticación y Seguridad (JWT) ---
    # Login Personalizado: Devuelve Access Token + Refresh Token + Rol + SocioID
    path('api/v1/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # Refresh Token: Para obtener un nuevo access token cuando el anterior expira
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # --- 3. Endpoints de Negocio (Tus Adaptadores) ---
    # Aquí se conectan Barrios, Terrenos, Medidores, Socios, Facturas, etc.
    path('api/v1/', include('adapters.api.urls')),

    # --- 4. Documentación Interactiva (Swagger/Redoc) ---
    # UI estilo Swagger (La más común y recomendada)
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # Archivo JSON crudo (útil para importar en Postman si quisieras)
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # UI estilo Redoc (Alternativa más moderna visualmente)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]