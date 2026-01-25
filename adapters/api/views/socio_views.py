# adapters/api/views/socio_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser 
from drf_yasg.utils import swagger_auto_schema # <--- IMPORTANTE PARA DOCUMENTACIÓN

# Importamos los "traductores" de BBDD
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.repositories.django_auth_repository import DjangoAuthRepository

# Importamos los "porteros" (Serializers)
from adapters.api.serializers.socio_serializers import (
    SocioSerializer, CrearSocioSerializer, ActualizarSocioSerializer
)
# Importamos los "cerebros" (Use Cases) y DTOs
from core.use_cases.socio_uc import (
    ListarSociosUseCase, ObtenerSocioUseCase, CrearSocioUseCase, 
    ActualizarSocioUseCase, EliminarSocioUseCase
)
from core.use_cases.socio_dtos import CrearSocioDTO, ActualizarSocioDTO
# Importamos las excepciones de negocio
from core.shared.exceptions import SocioNoEncontradoError, ValidacionError

class SocioViewSet(viewsets.ViewSet):
    """
    ViewSet (Ventanilla) para la gestión CRUD de Socios.
    """
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(responses={200: SocioSerializer(many=True)})
    def list(self, request):
        """ GET /api/v1/socios/ """
        try:
            repo = DjangoSocioRepository()
            use_case = ListarSociosUseCase(repo)
            socios_dto = use_case.execute()
            serializer = SocioSerializer(socios_dto, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(responses={200: SocioSerializer()})
    def retrieve(self, request, pk=None):
        """ GET /api/v1/socios/<pk>/ """
        repo = DjangoSocioRepository()
        use_case = ObtenerSocioUseCase(repo)
        try:
            socio_dto = use_case.execute(socio_id=int(pk))
            serializer = SocioSerializer(socio_dto)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SocioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=CrearSocioSerializer, responses={201: SocioSerializer()})
    def create(self, request):
        """ POST /api/v1/socios/ """
        try:
            serializer = CrearSocioSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # MAGIA PYTHONICA: Como los campos del Serializer se llaman IGUAL
            # que los del DTO (barrio_id, direccion), podemos desempaquetar con **
            crear_dto = CrearSocioDTO(**serializer.validated_data)
            
            socio_repo = DjangoSocioRepository()
            auth_repo = DjangoAuthRepository()
            
            use_case = CrearSocioUseCase(socio_repo, auth_repo)
            
            socio_creado_dto = use_case.execute(crear_dto)
            response_serializer = SocioSerializer(socio_creado_dto)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        """ PUT /api/v1/socios/<pk>/ (Redirige a PATCH) """
        return self.partial_update(request, pk)

    @swagger_auto_schema(request_body=ActualizarSocioSerializer, responses={200: SocioSerializer()})
    def partial_update(self, request, pk=None):
        """ PATCH /api/v1/socios/<pk>/ """
        serializer = ActualizarSocioSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        actualizar_dto = ActualizarSocioDTO(**serializer.validated_data)

        socio_repo = DjangoSocioRepository()
        auth_repo = DjangoAuthRepository()
        
        use_case = ActualizarSocioUseCase(socio_repo, auth_repo)
        
        try:
            socio_actualizado_dto = use_case.execute(int(pk), actualizar_dto)
            response_serializer = SocioSerializer(socio_actualizado_dto)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except SocioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """ DELETE /api/v1/socios/<pk>/ """
        socio_repo = DjangoSocioRepository()
        auth_repo = DjangoAuthRepository()
        
        use_case = EliminarSocioUseCase(socio_repo, auth_repo)
        
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SocioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)