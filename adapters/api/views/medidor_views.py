# adapters/api/views/medidor_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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

# ✅ 1. PERMISO PERSONALIZADO (Propuesta Frontend mejorada)
class IsAdminOrOperador(BasePermission):
    """
    Permite escritura solo a Staff, Admins, Operadores o Tesoreros.
    Lectura permitida a cualquiera autenticado (controlada en la vista).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Si es método de lectura segura (GET, HEAD, OPTIONS), dejamos pasar
        # (El filtro de datos se hará dentro de list/retrieve)
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Para escribir (POST, PUT, DELETE), verificamos ROL
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

    # ======================================================
    # LISTAR (Con Filtro de Seguridad)
    # ======================================================
    @swagger_auto_schema(
        operation_description="Lista medidores. Admins ven todos, Socios solo los suyos.",
        responses={200: MedidorSerializer(many=True)}
    )
    def list(self, request):
        repo = DjangoMedidorRepository()
        use_case = ListarMedidoresUseCase(repo)

        # 1. Traemos todo (Para 240 socios es aceptable hacerlo en memoria)
        medidores = use_case.execute()

        # 2. Filtro de Seguridad
        user = request.user
        es_personal_tecnico = False

        if user.is_staff or user.is_superuser:
            es_personal_tecnico = True
        elif hasattr(user, 'perfil_socio') and user.perfil_socio:
            rol = str(user.perfil_socio.rol).upper()
            if rol in ['ADMIN', 'OPERADOR', 'TESORERO']:
                es_personal_tecnico = True

        # Si NO es técnico (es un Socio común), filtramos
        if not es_personal_tecnico:
            medidores_filtrados = []
            for m in medidores:
                try:
                    # Navegamos: Medidor -> Terreno -> Socio -> Usuario
                    if m.terreno and m.terreno.socio and m.terreno.socio.usuario_id == user.id:
                        medidores_filtrados.append(m)
                except AttributeError:
                    continue
            medidores = medidores_filtrados

        serializer = MedidorSerializer(medidores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ======================================================
    # PLANILLA DE LECTURAS (CORREGIDO - FILTRO REAL EN BD)
    # ======================================================
    @action(detail=False, methods=['get'], url_path='planilla-lecturas')
    def planilla_lecturas(self, request):
        """
        Devuelve los medidores ACTIVOS filtrados por Barrio directamente desde la BD.
        """
        # 1. Obtenemos el parámetro del filtro
        barrio_param = request.query_params.get('barrio')

        # 2. QuerySet Base: Traer solo medidores ACTIVOS
        # Usamos el Modelo directamente para aprovechar el motor de base de datos
        queryset = MedidorModel.objects.filter(estado='ACTIVO')

        # 3. Filtro Inteligente por Barrio
        if barrio_param and barrio_param != 'null' and barrio_param != '':
            # Django ORM permite navegar las relaciones con doble guion bajo "__"
            # terreno__barrio__nombre__iexact significa:
            # "Entra al Terreno, luego al Barrio, busca el Nombre (insensible a mayúsculas/minúsculas)"
            queryset = queryset.filter(terreno__barrio__nombre__iexact=barrio_param.strip())

        # 4. Optimizamos la consulta para traer los datos relacionados de una sola vez
        # (select_related evita que el sistema haga 100 consultas si hay 100 medidores)
        queryset = queryset.select_related('terreno', 'terreno__socio')

        # 5. Serializamos
        # El serializer funciona igual de bien con Modelos que con Entidades
        serializer = MedidorSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    # ======================================================
    # OBTENER UNO
    # ======================================================
    @swagger_auto_schema(responses={200: MedidorSerializer(), 404: "No encontrado"})
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
    @swagger_auto_schema(
        request_body=RegistrarMedidorSerializer,
        responses={201: MedidorSerializer(), 400: "Error validación"}
    )
    def create(self, request):
        serializer = RegistrarMedidorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Usamos el DTO correcto que tú ya tenías
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
    # ACTUALIZAR (Solo Técnicos)
    # ======================================================
    def update(self, request, pk=None):
        return self.partial_update(request, pk)

    @swagger_auto_schema(
        request_body=ActualizarMedidorSerializer,
        responses={200: MedidorSerializer(), 404: "No encontrado"}
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
    # ELIMINAR (Solo Técnicos)
    # ======================================================
    @swagger_auto_schema(responses={204: "Eliminado"})
    def destroy(self, request, pk=None):
        repo = DjangoMedidorRepository()
        use_case = EliminarMedidorUseCase(repo)
        try:
            use_case.execute(int(pk))
            return Response(status=status.HTTP_204_NO_CONTENT)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        # ======================================================
    # OBTENER MI MEDIDOR (Para el panel del Socio)
    # ======================================================
    @action(detail=False, methods=['get'], url_path='mi-medidor', permission_classes=[IsAuthenticated])
    def mi_medidor(self, request):
        """
        Endpoint exclusivo para que el socio logueado vea su medidor.
        """
        user = request.user

        # 1. Buscamos el medidor usando el Modelo directamente para mayor seguridad
        # Navegamos: Medidor -> Terreno -> Socio -> Usuario
        medidor = MedidorModel.objects.filter(
            terreno__socio__usuario_id=user.id
        ).select_related('terreno', 'terreno__socio', 'terreno__barrio').first()

        if not medidor:
            return Response(
                {"error": "No tienes un medidor asignado a tu cuenta de usuario."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. Usamos tu serializer existente
        serializer = MedidorSerializer(medidor)
        return Response(serializer.data, status=status.HTTP_200_OK)