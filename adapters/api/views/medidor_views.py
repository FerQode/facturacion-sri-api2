# adapters/api/views/medidor_views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

# --- CAPA DE INFRAESTRUCTURA (REPOSITORIOS) ---
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_terreno_repository import DjangoTerrenoRepository

# --- CAPA DE PRESENTACIÓN (SERIALIZERS) ---
from adapters.api.serializers.medidor_serializers import (
    MedidorSerializer,              # Output
    RegistrarMedidorSerializer,     # Input (Nombre coincide con tu DTO)
    ActualizarMedidorSerializer     # Input
)

# --- CAPA DE APLICACIÓN (CASOS DE USO) ---
# Importamos la lógica de negocio desde medidor_uc.py
from core.use_cases.medidor_uc import (
    ListarMedidoresUseCase, 
    ObtenerMedidorUseCase, 
    CrearMedidorUseCase,      # OJO: El caso de uso se llama 'Crear...', aunque recibe un 'RegistrarDTO'
    ActualizarMedidorUseCase, 
    EliminarMedidorUseCase
)

# --- DTOS (CORRECCIÓN DEFINITIVA) ---
# Importamos desde el archivo ESPECÍFICO 'medidor_dtos.py'
# Y usamos el nombre REAL que me mostraste: 'RegistrarMedidorDTO'
from core.use_cases.medidor_dtos import (
    RegistrarMedidorDTO,   # <--- ESTE ERA EL CULPABLE (Antes buscábamos CrearMedidorDTO)
    ActualizarMedidorDTO
)

# --- EXCEPCIONES ---
from core.shared.exceptions import (
    MedidorNoEncontradoError, 
    TerrenoNoEncontradoError,
    ValidacionError
)

class MedidorViewSet(viewsets.ViewSet):
    """
    ViewSet para la gestión CRUD completa de Medidores.
    """
    permission_classes = [IsAdminUser]

    def list(self, request):
        """ GET /api/v1/medidores/ """
        repo = DjangoMedidorRepository()
        use_case = ListarMedidoresUseCase(repo)
        medidores = use_case.execute()
        serializer = MedidorSerializer(medidores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """ GET /api/v1/medidores/<pk>/ """
        repo = DjangoMedidorRepository()
        use_case = ObtenerMedidorUseCase(repo)
        try:
            medidor = use_case.execute(int(pk))
            return Response(MedidorSerializer(medidor).data, status=status.HTTP_200_OK)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        """ POST /api/v1/medidores/ """
        # 1. Validar entrada (Serializer)
        serializer = RegistrarMedidorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Convertir a DTO
        # CORRECCIÓN: Usamos la clase que existe en medidor_dtos.py
        dto = RegistrarMedidorDTO(**serializer.validated_data)
        
        # 3. Dependencias
        medidor_repo = DjangoMedidorRepository()
        terreno_repo = DjangoTerrenoRepository()
        
        # 4. Caso de Uso
        # Nota: El Caso de Uso 'CrearMedidorUseCase' debe estar preparado para recibir 'RegistrarMedidorDTO'
        use_case = CrearMedidorUseCase(medidor_repo, terreno_repo)
        
        try:
            nuevo_medidor = use_case.execute(dto)
            return Response(MedidorSerializer(nuevo_medidor).data, status=status.HTTP_201_CREATED)
        
        except TerrenoNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        return self.partial_update(request, pk)

    def partial_update(self, request, pk=None):
        serializer = ActualizarMedidorSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        dto = ActualizarMedidorDTO(**serializer.validated_data)
        medidor_repo = DjangoMedidorRepository()
        
        # Ajustar si tu constructor requiere más repositorios
        use_case = ActualizarMedidorUseCase(medidor_repo) 
        
        try:
            medidor_actualizado = use_case.execute(int(pk), dto)
            return Response(MedidorSerializer(medidor_actualizado).data, status=status.HTTP_200_OK)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        repo = DjangoMedidorRepository()
        use_case = EliminarMedidorUseCase(repo)
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)