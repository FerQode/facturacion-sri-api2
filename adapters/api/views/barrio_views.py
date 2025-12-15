# adapters/api/views/barrio_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

# Repositorio (Infraestructura)
from adapters.infrastructure.repositories.django_barrio_repository import DjangoBarrioRepository

# Serializers (Porteros)
from adapters.api.serializers.barrio_serializers import (
    BarrioSerializer, CrearBarrioSerializer, ActualizarBarrioSerializer
)

# Casos de Uso (Cerebro) y DTOs
from core.use_cases.barrio_uc import (
    ListarBarriosUseCase, ObtenerBarrioUseCase, CrearBarrioUseCase, 
    ActualizarBarrioUseCase, EliminarBarrioUseCase
)
from core.use_cases.barrio_dtos import CrearBarrioDTO, ActualizarBarrioDTO

# Excepciones de Negocio
from core.shared.exceptions import ValidacionError, BaseExcepcionDeNegocio

# Si tienes una excepción específica para Barrio, impórtala también. 
# Si la definiste dentro de barrio_uc.py, impórtala desde ahí:
from core.use_cases.barrio_uc import BarrioNoEncontradoError

class BarrioViewSet(viewsets.ViewSet):
    """
    ViewSet para la gestión CRUD de Barrios.
    """

    def get_permissions(self):
        """
        Permisos diferenciados por acción:
        - Listar/Ver: Cualquier usuario autenticado.
        - Crear/Editar/Borrar: Solo Administradores.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def list(self, request):
        """ GET /api/v1/barrios/ """
        repo = DjangoBarrioRepository()
        use_case = ListarBarriosUseCase(repo)
        
        dtos = use_case.execute()
        
        serializer = BarrioSerializer(dtos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """ GET /api/v1/barrios/<pk>/ """
        repo = DjangoBarrioRepository()
        use_case = ObtenerBarrioUseCase(repo)
        
        try:
            dto = use_case.execute(int(pk))
            return Response(BarrioSerializer(dto).data, status=status.HTTP_200_OK)
        except BarrioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """ POST /api/v1/barrios/ """
        serializer = CrearBarrioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        dto = CrearBarrioDTO(**serializer.validated_data)
        repo = DjangoBarrioRepository()
        use_case = CrearBarrioUseCase(repo)
        
        try:
            result = use_case.execute(dto)
            return Response(BarrioSerializer(result).data, status=status.HTTP_201_CREATED)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """ PUT /api/v1/barrios/<pk>/ """
        return self.partial_update(request, pk)

    def partial_update(self, request, pk=None):
        """ PATCH /api/v1/barrios/<pk>/ """
        serializer = ActualizarBarrioSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        dto = ActualizarBarrioDTO(**serializer.validated_data)
        repo = DjangoBarrioRepository()
        use_case = ActualizarBarrioUseCase(repo)
        
        try:
            result = use_case.execute(int(pk), dto)
            return Response(BarrioSerializer(result).data, status=status.HTTP_200_OK)
        except BarrioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """ DELETE /api/v1/barrios/<pk>/ """
        repo = DjangoBarrioRepository()
        use_case = EliminarBarrioUseCase(repo)
        
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BarrioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)