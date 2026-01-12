from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema # ✅ Importamos Swagger
from drf_yasg import openapi

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

# Excepciones
from core.shared.exceptions import ValidacionError
from core.use_cases.barrio_uc import BarrioNoEncontradoError

class BarrioViewSet(viewsets.ViewSet):
    """
    ViewSet para la gestión de Barrios.
    """

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    # ✅ DOCUMENTACIÓN VISUAL PARA EL FRONTEND
    @swagger_auto_schema(
        operation_summary="Listar todos los barrios",
        responses={200: BarrioSerializer(many=True)}
    )
    def list(self, request):
        repo = DjangoBarrioRepository()
        use_case = ListarBarriosUseCase(repo)
        
        dtos = use_case.execute()
        
        serializer = BarrioSerializer(dtos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Obtener un barrio por ID",
        responses={200: BarrioSerializer(), 404: "No encontrado"}
    )
    def retrieve(self, request, pk=None):
        repo = DjangoBarrioRepository()
        use_case = ObtenerBarrioUseCase(repo)
        
        try:
            dto = use_case.execute(int(pk))
            return Response(BarrioSerializer(dto).data, status=status.HTTP_200_OK)
        except BarrioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Crear un nuevo barrio",
        request_body=CrearBarrioSerializer,
        responses={201: BarrioSerializer(), 400: "Error de validación"}
    )
    def create(self, request):
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
        return self.partial_update(request, pk)

    @swagger_auto_schema(
        operation_summary="Actualizar un barrio",
        request_body=ActualizarBarrioSerializer,
        responses={200: BarrioSerializer(), 404: "No encontrado"}
    )
    def partial_update(self, request, pk=None):
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

    @swagger_auto_schema(
        operation_summary="Eliminar un barrio",
        responses={204: "Eliminado correctamente", 404: "No encontrado"}
    )
    def destroy(self, request, pk=None):
        repo = DjangoBarrioRepository()
        use_case = EliminarBarrioUseCase(repo)
        
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BarrioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)