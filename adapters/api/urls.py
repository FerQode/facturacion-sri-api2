from django.urls import path

# Importamos las Vistas (Views) que conectan con los Casos de Uso
# (Asumimos que el archivo se llama 'lectura_views.py' como en el ejemplo anterior)
from .views import lectura_views 

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
]