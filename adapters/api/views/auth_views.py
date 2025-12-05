# adapters/api/views/auth_views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from adapters.api.serializers.auth_serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista de login personalizada que devuelve tokens con Claims extra (rol, id).
    Hereda de la vista estándar de SimpleJWT pero inyecta nuestro serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer