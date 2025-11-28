# adapters/api/views/socio_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser # <-- ¡Mejora de Seguridad!

# Importamos los "traductores" de BBDD
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
# --- NUEVO IMPORT ---
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
    Cada método llama a su Caso de Uso correspondiente,
    manteniendo la Arquitectura Limpia.
    
    BUENA PRÁCTICA: Usamos IsAdminUser (requiere is_staff=True)
    para asegurar que solo Administradores o Tesoreros puedan
    gestionar socios.
    """
    permission_classes = [IsAdminUser]

    def list(self, request):
        """ GET /api/v1/socios/ """
        repo = DjangoSocioRepository()
        use_case = ListarSociosUseCase(repo)
        socios_dto = use_case.execute()
        serializer = SocioSerializer(socios_dto, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    def create(self, request):
        """ POST /api/v1/socios/ """
        # 1. Validar con el "Portero"
        serializer = CrearSocioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Crear el DTO para el "Cerebro"
        crear_dto = CrearSocioDTO(**serializer.validated_data)
        
        # 3. Ejecutar el "Cerebro"
        socio_repo = DjangoSocioRepository()
        auth_repo = DjangoAuthRepository() # <-- Instanciamos el repo de Auth
        
        # --- PASAMOS AMBOS REPOS ---
        use_case = CrearSocioUseCase(socio_repo, auth_repo)
        
        try:
            socio_creado_dto = use_case.execute(crear_dto)
            # 4. Devolver la respuesta
            response_serializer = SocioSerializer(socio_creado_dto)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, pk=None):
        """ PUT /api/v1/socios/<pk>/ (Maneja PUT como PATCH) """
        return self.partial_update(request, pk)

    def partial_update(self, request, pk=None):
        """ PATCH /api/v1/socios/<pk>/ """
        # 1. Validar con el "Portero"
        serializer = ActualizarSocioSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Crear el DTO
        actualizar_dto = ActualizarSocioDTO(**serializer.validated_data)

        # 3. Ejecutar el "Cerebro"
        repo = DjangoSocioRepository()
        use_case = ActualizarSocioUseCase(repo)
        try:
            socio_actualizado_dto = use_case.execute(int(pk), actualizar_dto)
            # 4. Devolver respuesta
            response_serializer = SocioSerializer(socio_actualizado_dto)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except SocioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        """ DELETE /api/v1/socios/<pk>/ """
        socio_repo = DjangoSocioRepository()
        auth_repo = DjangoAuthRepository() # <-- Instanciamos el repo de Auth
        
        # --- TAMBIÉN AQUÍ NECESITAMOS LOS DOS REPOS ---
        use_case = EliminarSocioUseCase(socio_repo, auth_repo)
        
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SocioNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)