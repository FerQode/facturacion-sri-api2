# adapters/api/views/lectura_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Core
from core.use_cases.registrar_lectura_uc import RegistrarLecturaUseCase
from core.shared.exceptions import MedidorNoEncontradoError, BusinessRuleException, EntityNotFoundException

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

    def _get_repos(self):
        return {
            "lectura": DjangoLecturaRepository(),
            "medidor": DjangoMedidorRepository()
        }

    # ======================================================
    # 1. REGISTRAR LECTURA (POST)
    # ======================================================
    @swagger_auto_schema(request_body=RegistrarLecturaSerializer, responses={201: LecturaResponseSerializer})
    def create(self, request):
        # 1. Validar entrada
        input_serializer = RegistrarLecturaSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            repos = self._get_repos()
            use_case = RegistrarLecturaUseCase(
                lectura_repo=repos['lectura'], 
                medidor_repo=repos['medidor']
            )
            
            # 2. Ejecutar lógica de negocio (usando el DTO del serializer)
            lectura_creada = use_case.ejecutar(input_serializer.to_dto())
            
            # 3. Responder con formato estándar
            response_serializer = LecturaResponseSerializer(lectura_creada)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except (MedidorNoEncontradoError, BusinessRuleException, EntityNotFoundException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ======================================================
    # 2. LISTAR HISTORIAL (GET)
    # ======================================================
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('medidor_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Filtrar por medidor"),
            openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Límite (default 12)"),
        ],
        responses={200: LecturaHistorialSerializer(many=True)}
    )
    def list(self, request):
        medidor_id = request.query_params.get('medidor_id')
        limit = int(request.query_params.get('limit', 12))

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