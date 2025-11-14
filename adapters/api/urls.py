from django.urls import path

# Importamos las Vistas (Views) que conectan con los Casos de Uso
# (Asumimos que el archivo se llama 'lectura_views.py' como en el ejemplo anterior)
from .views import lectura_views
from .views import factura_views

# Estos son los endpoints específicos de la API
urlpatterns = [
    # Cuando alguien llame a .../api/v1/lecturas/registrar/
    path(
        'lecturas/registrar/', 
        lectura_views.RegistrarLecturaAPIView.as_view(), 
        name='registrar-lectura'
    ),

    # --- Aquí añadirás las otras vistas ---
    # path('socios/crear/', tu_vista_socio.as_view(), name='crear-socio'),
    # path('facturas/enviar-sri/', tu_vista_factura.as_view(), name='enviar-factura'),
    # --- ENDPOINT NUEVO (PASO 4) ---
    # Endpoint 2: Generar Factura
    # Cuando un cliente llame a 'api/v1/facturas/generar/',
    # Django llamará a nuestra clase GenerarFacturaAPIView.
    path(
        'facturas/generar/', 
        factura_views.GenerarFacturaAPIView.as_view(), 
        name='generar-factura'
    ),

    # --- ENDPOINT NUEVO (PASO 3 DE LA TESIS) ---
    # Endpoint 3: Enviar Factura al SRI
    path(
        'facturas/enviar-sri/', 
        factura_views.EnviarFacturaSRIAPIView.as_view(), 
        name='enviar-factura-sri'
    ),

]