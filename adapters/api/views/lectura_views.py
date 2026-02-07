# adapters/api/views/lectura_views.py
import dataclasses # ✅ Necesario para la inyección segura de usuario
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

# Core
from core.use_cases.registrar_lectura_uc import RegistrarLecturaUseCase
from core.shared.exceptions import (
    MedidorNoEncontradoError, 
    BusinessRuleException, 
    EntityNotFoundException,
    ValidacionError
)

# Infraestructura
from adapters.infrastructure.repositories.django_lectura_repository import DjangoLecturaRepository
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.models import LecturaModel # Para listado eficiente

# Serializers
from adapters.api.serializers.lectura_serializers import (
    RegistrarLecturaSerializer, 
    LecturaResponseSerializer,
    LecturaHistorialSerializer
)

class LecturaViewSet(viewsets.ViewSet):
    """
    Gestión de Lecturas:
    - POST: Registrar nueva lectura (Caso de Uso).
    - GET: Listar historial (Consulta optimizada).
    """
    
    # Aseguramos que solo usuarios logueados puedan registrar lecturas
    permission_classes = [IsAuthenticated]

    def _get_repos(self):
        return {
            "lectura": DjangoLecturaRepository(),
            "medidor": DjangoMedidorRepository()
        }

    # ======================================================
    # 1. REGISTRAR LECTURA (POST)
    # ======================================================
    @extend_schema(
        summary="Registrar Lectura",
        description="Registra una nueva lectura de medidor.",
        request=RegistrarLecturaSerializer, 
        responses={201: LecturaResponseSerializer}
    )
    def create(self, request):
        # 1. Validar entrada (JSON)
        input_serializer = RegistrarLecturaSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            repos = self._get_repos()
            use_case = RegistrarLecturaUseCase(
                lectura_repo=repos['lectura'], 
                medidor_repo=repos['medidor']
            )
            
            # 2. Preparar DTO con Datos Seguros
            dto_temporal = input_serializer.to_dto()
            
            # ✅ MEJORA: Inyectamos el ID real del usuario logueado
            # Si por alguna razón no hay usuario (ej: test), usamos 1 por defecto
            real_operador_id = request.user.id if request.user and request.user.is_authenticated else 1
            
            # Reemplazamos el operador_id en el DTO sin mutar el original
            dto_final = dataclasses.replace(dto_temporal, operador_id=real_operador_id)

            # 3. Ejecutar Lógica de Negocio
            lectura_creada = use_case.ejecutar(dto_final) # Nota: Verifica si tu UC usa 'ejecutar' o 'execute'
            
            # 4. Responder
            response_serializer = LecturaResponseSerializer(lectura_creada)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except (MedidorNoEncontradoError, BusinessRuleException, EntityNotFoundException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Loguear error real en consola para debugging
            print(f"❌ ERROR LECTURAS: {str(e)}")
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ======================================================
    # 2. LISTAR HISTORIAL (GET)
    # ======================================================
    @extend_schema(
        summary="Listar Historial de Lecturas",
        description="Obtiene el historial de lecturas registradas.",
        parameters=[
            OpenApiParameter('medidor_id', description="Filtrar por medidor", required=False, type=int),
            OpenApiParameter('limit', description="Límite (default 12)", required=False, type=int),
        ],
        responses={200: LecturaHistorialSerializer(many=True)}
    )
    def list(self, request):
        medidor_id = request.query_params.get('medidor_id')
        try:
            limit = int(request.query_params.get('limit', 12))
        except ValueError:
            limit = 12

        # QuerySet optimizado con select_related para evitar el problema N+1 queries
        queryset = LecturaModel.objects.select_related(
            'medidor', 
            'medidor__terreno', 
            'medidor__terreno__socio'
        ).all().order_by('-fecha')

        if medidor_id:
            queryset = queryset.filter(medidor_id=medidor_id)

        # Límite de seguridad
        queryset = queryset[:limit]

        serializer = LecturaHistorialSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)