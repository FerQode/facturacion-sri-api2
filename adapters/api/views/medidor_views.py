# adapters/api/views/medidor_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

# --- CAPA DE INFRAESTRUCTURA ---
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_terreno_repository import DjangoTerrenoRepository
from adapters.infrastructure.models import MedidorModel
# --- CAPA DE PRESENTACIÓN ---
from adapters.api.serializers.medidor_serializers import (
    MedidorSerializer,
    RegistrarMedidorSerializer,
    ActualizarMedidorSerializer
)

# --- CAPA DE APLICACIÓN ---
from core.use_cases.medidor_uc import (
    ListarMedidoresUseCase,
    ObtenerMedidorUseCase,
    CrearMedidorUseCase,
    ActualizarMedidorUseCase,
    EliminarMedidorUseCase
)

# --- DTOS ---
from core.use_cases.medidor_dtos import (
    RegistrarMedidorDTO,
    ActualizarMedidorDTO
)

# --- EXCEPCIONES ---
from core.shared.exceptions import (
    MedidorNoEncontradoError,
    TerrenoNoEncontradoError,
    ValidacionError
)

# ✅ 1. PERMISO PERSONALIZADO
class IsAdminOrOperador(BasePermission):
    """
    Permite escritura solo a Staff, Admins, Operadores o Tesoreros.
    Lectura permitida a cualquiera autenticado (controlada en la vista).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True
        if hasattr(request.user, 'perfil_socio') and request.user.perfil_socio:
            rol = str(request.user.perfil_socio.rol).upper()
            return rol in ['ADMIN', 'OPERADOR', 'TESORERO']
        return False

class MedidorViewSet(viewsets.ViewSet):
    """
    Gestión de Medidores (Inventario).
    """
    permission_classes = [IsAdminOrOperador]
    
    # IMPORTANTE: Definir serializer base para 'unable to guess' warnings
    serializer_class = MedidorSerializer

    # ======================================================
    # LISTAR (Con Filtro de Seguridad)
    # ======================================================
    @extend_schema(
        summary="Listar Medidores",
        description="Lista medidores. Admins ven todos, Socios solo los suyos.",
        responses={200: MedidorSerializer(many=True)}
    )
    def list(self, request):
        repo = DjangoMedidorRepository()
        use_case = ListarMedidoresUseCase(repo)
        medidores = use_case.execute()

        # Filtro de Seguridad
        user = request.user
        es_personal_tecnico = False

        if user.is_staff or user.is_superuser:
            es_personal_tecnico = True
        elif hasattr(user, 'perfil_socio') and user.perfil_socio:
            rol = str(user.perfil_socio.rol).upper()
            if rol in ['ADMIN', 'OPERADOR', 'TESORERO']:
                es_personal_tecnico = True

        if not es_personal_tecnico:
            medidores_filtrados = []
            for m in medidores:
                try:
                    if m.terreno and m.terreno.socio and m.terreno.socio.usuario_id == user.id:
                        medidores_filtrados.append(m)
                except AttributeError:
                    continue
            medidores = medidores_filtrados

        serializer = MedidorSerializer(medidores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ======================================================
    # PLANILLA DE LECTURAS
    # ======================================================
    @extend_schema(
        summary="Planilla de Lecturas",
        description="Obtiene medidores ACTIVOS para registro de lecturas, filtrables por barrio.",
        parameters=[OpenApiParameter("barrio", OpenApiTypes.STR, description="Nombre del barrio para filtrar")],
        responses={200: MedidorSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='planilla-lecturas')
    def planilla_lecturas(self, request):
        barrio_param = request.query_params.get('barrio')
        queryset = MedidorModel.objects.filter(estado='ACTIVO')

        if barrio_param and barrio_param != 'null' and barrio_param != '':
            queryset = queryset.filter(terreno__barrio__nombre__iexact=barrio_param.strip())

        queryset = queryset.select_related('terreno', 'terreno__socio')
        serializer = MedidorSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ======================================================
    # OBTENER UNO
    # ======================================================
    @extend_schema(
        summary="Obtener Medidor Detallado",
        parameters=[OpenApiParameter("id", OpenApiTypes.INT, location=OpenApiParameter.PATH)],
        responses={200: MedidorSerializer(), 404: OpenApiTypes.OBJECT}
    )
    def retrieve(self, request, pk=None):
        repo = DjangoMedidorRepository()
        use_case = ObtenerMedidorUseCase(repo)
        try:
            medidor = use_case.execute(int(pk))
            return Response(MedidorSerializer(medidor).data, status=status.HTTP_200_OK)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    # ======================================================
    # CREAR (Solo Técnicos)
    # ======================================================
    @extend_schema(
        summary="Registrar Nuevo Medidor",
        request=RegistrarMedidorSerializer,
        responses={201: MedidorSerializer(), 400: OpenApiTypes.OBJECT}
    )
    def create(self, request):
        serializer = RegistrarMedidorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dto = RegistrarMedidorDTO(**serializer.validated_data)
        medidor_repo = DjangoMedidorRepository()
        terreno_repo = DjangoTerrenoRepository()
        use_case = CrearMedidorUseCase(medidor_repo, terreno_repo)

        try:
            nuevo_medidor = use_case.execute(dto)
            return Response(MedidorSerializer(nuevo_medidor).data, status=status.HTTP_201_CREATED)
        except (TerrenoNoEncontradoError, ValidacionError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ======================================================
    # ACTUALIZAR
    # ======================================================
    @extend_schema(exclude=True)
    def update(self, request, pk=None):
        return self.partial_update(request, pk)

    @extend_schema(
        summary="Actualizar Medidor",
        request=ActualizarMedidorSerializer,
        parameters=[OpenApiParameter("id", OpenApiTypes.INT, location=OpenApiParameter.PATH)],
        responses={200: MedidorSerializer(), 404: OpenApiTypes.OBJECT}
    )
    def partial_update(self, request, pk=None):
        serializer = ActualizarMedidorSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dto = ActualizarMedidorDTO(**serializer.validated_data)
        medidor_repo = DjangoMedidorRepository()
        use_case = ActualizarMedidorUseCase(medidor_repo)

        try:
            medidor_actualizado = use_case.execute(int(pk), dto)
            return Response(MedidorSerializer(medidor_actualizado).data, status=status.HTTP_200_OK)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ======================================================
    # ELIMINAR
    # ======================================================
    @extend_schema(
        summary="Dar de Baja Medidor",
        parameters=[OpenApiParameter("id", OpenApiTypes.INT, location=OpenApiParameter.PATH)],
        responses={204: None, 404: OpenApiTypes.OBJECT}
    )
    def destroy(self, request, pk=None):
        repo = DjangoMedidorRepository()
        use_case = EliminarMedidorUseCase(repo)
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    # ======================================================
    # MI MEDIDOR
    # ======================================================
    @extend_schema(
        summary="Mi Medidor (Info Socio)",
        description="Obtiene el medidor asociado al socio logueado.",
        responses={200: MedidorSerializer(), 404: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='mi-medidor', permission_classes=[IsAuthenticated])
    def mi_medidor(self, request):
        user = request.user
        medidor = MedidorModel.objects.filter(
            terreno__socio__usuario_id=user.id
        ).select_related('terreno', 'terreno__socio', 'terreno__barrio').first()

        if not medidor:
            return Response(
                {"error": "No tienes un medidor asignado a tu cuenta de usuario."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MedidorSerializer(medidor)
        return Response(serializer.data, status=status.HTTP_200_OK)