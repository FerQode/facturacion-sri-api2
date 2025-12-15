# adapters/api/views/medidor_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

# Repositorios (Infraestructura)
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository

# Serializers (Porteros)
from adapters.api.serializers.medidor_serializers import (
    MedidorSerializer, CrearMedidorSerializer, ActualizarMedidorSerializer
)

# Casos de Uso (Cerebro) y DTOs
from core.use_cases.medidor_uc import (
    ListarMedidoresUseCase, ObtenerMedidorUseCase, CrearMedidorUseCase, 
    ActualizarMedidorUseCase, EliminarMedidorUseCase
)
from core.use_cases.medidor_dtos import CrearMedidorDTO, ActualizarMedidorDTO

# Excepciones de Negocio
from core.shared.exceptions import MedidorNoEncontradoError, SocioNoEncontradoError, ValidacionError

class MedidorViewSet(viewsets.ViewSet):
    """
    ViewSet para la gestión CRUD de Medidores.
    Acceso restringido a Administradores/Tesoreros (IsAdminUser).
    """
    permission_classes = [IsAdminUser]

    def list(self, request):
        """ GET /api/v1/medidores/ """
        repo = DjangoMedidorRepository()
        use_case = ListarMedidoresUseCase(repo)
        
        # Ejecutar Caso de Uso
        dtos = use_case.execute()
        
        # Serializar respuesta
        serializer = MedidorSerializer(dtos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """ GET /api/v1/medidores/<pk>/ """
        repo = DjangoMedidorRepository()
        use_case = ObtenerMedidorUseCase(repo)
        
        try:
            dto = use_case.execute(int(pk))
            return Response(MedidorSerializer(dto).data, status=status.HTTP_200_OK)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """ POST /api/v1/medidores/ """
        # 1. Validar entrada (Serializer)
        serializer = CrearMedidorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Convertir a DTO
        dto = CrearMedidorDTO(**serializer.validated_data)
        
        # 3. Instanciar dependencias
        medidor_repo = DjangoMedidorRepository()
        socio_repo = DjangoSocioRepository() # Necesario para validar que el socio existe
        
        # 4. Ejecutar Caso de Uso
        use_case = CrearMedidorUseCase(medidor_repo, socio_repo)
        
        try:
            result = use_case.execute(dto)
            return Response(MedidorSerializer(result).data, status=status.HTTP_201_CREATED)
        
        # 5. Manejo de Errores de Negocio
        except (SocioNoEncontradoError, ValidacionError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """ PUT /api/v1/medidores/<pk>/ """
        return self.partial_update(request, pk)

    def partial_update(self, request, pk=None):
        """ PATCH /api/v1/medidores/<pk>/ """
        # 1. Validar entrada
        serializer = ActualizarMedidorSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. DTO
        dto = ActualizarMedidorDTO(**serializer.validated_data)
        
        # 3. Dependencias
        medidor_repo = DjangoMedidorRepository()
        socio_repo = DjangoSocioRepository() # Necesario si se intenta cambiar el dueño
        
        # 4. Caso de Uso
        use_case = ActualizarMedidorUseCase(medidor_repo, socio_repo)
        
        try:
            result = use_case.execute(int(pk), dto)
            return Response(MedidorSerializer(result).data, status=status.HTTP_200_OK)
        
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except (SocioNoEncontradoError, ValidacionError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """ DELETE /api/v1/medidores/<pk>/ """
        repo = DjangoMedidorRepository()
        use_case = EliminarMedidorUseCase(repo)
        
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)