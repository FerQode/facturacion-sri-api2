from rest_framework import viewsets, permissions
from adapters.infrastructure.models import ServicioModel
from adapters.api.serializers.servicio_agua_serializers import ServicioAguaSerializer

class ServicioAguaViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para gestionar Servicios de Agua (Tarifa Fija).
    Permite: Crear (POST), Listar (GET), Actualizar (PUT/PATCH) y Borrar (DELETE).
    """
    queryset = ServicioModel.objects.all()
    serializer_class = ServicioAguaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Opcional: Si quisieras filtrar por barrio o activo en la URL
        Ej: /servicios-agua/?activo=true
        """
        queryset = super().get_queryset()
        activo = self.request.query_params.get('activo')
        if activo is not None:
            es_activo = activo.lower() == 'true'
            queryset = queryset.filter(activo=es_activo)
        return queryset