"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# --- AÑADIDO: Importamos nuestra vista personalizada ---
from adapters.api.views.auth_views import CustomTokenObtainPairView

# Importamos la vista de refresh (esa la usamos tal cual de la librería)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- MODIFICADO: Endpoint de Login ---
    # Usamos CustomTokenObtainPairView en lugar de la vista por defecto (TokenObtainPairView).
    # Cuando el frontend llame aquí, recibirá el token con 'rol' y 'socio_id' en el payload.
    path('api/v1/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Endpoint de Refresh (estándar)
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rutas de la API (nuestros adaptadores)
    path('api/v1/', include('adapters.api.urls')),
]