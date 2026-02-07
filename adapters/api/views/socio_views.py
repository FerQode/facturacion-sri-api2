# adapters/api/views/socio_views.py
from django.db import transaction # IMPORTANTE PARA INTEGRIDAD
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
# ✅ CAMBIO CLAVE: Reemplazamos drf_yasg por drf_spectacular
from drf_spectacular.utils import extend_schema, OpenApiParameter

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

# --- IMPORTACIONES PARA ESTADO DE CUENTA 360 ---
from adapters.api.serializers.estado_cuenta_serializers import EstadoCuentaSerializer
from core.use_cases.socio.obtener_estado_cuenta_use_case import ObtenerEstadoCuentaUseCase
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.repositories.django_terreno_repository import DjangoTerrenoRepository
from adapters.infrastructure.repositories.django_pago_repository import DjangoPagoRepository
from adapters.infrastructure.repositories.django_servicio_repository import DjangoServicioRepository

class SocioViewSet(viewsets.ViewSet):
    """
    ViewSet (Ventanilla) para la gestión CRUD de Socios.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Listar Socios",
        description="Obtiene el listado paginado de todos los socios registrados.",
        responses={200: SocioSerializer(many=True)}
    )
    def list(self, request):
        """ GET /api/v1/socios/ """
        try:
            repo = DjangoSocioRepository()
            use_case = ListarSociosUseCase(repo)
            socios_dto = use_case.execute()
            
            # Paginación manual para ViewSet custom
            paginator = PageNumberPagination()
            paginator.page_size = 20 # Configuración por defecto
            result_page = paginator.paginate_queryset(socios_dto, request, view=self)
            
            if result_page is not None:
                serializer = SocioSerializer(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = SocioSerializer(socios_dto, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Obtener Socio",
        responses={200: SocioSerializer()}
    )
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

    @extend_schema(
        summary="Crear Socio",
        request=CrearSocioSerializer, # En spectacular se usa 'request', no 'request_body'
        responses={201: SocioSerializer()}
    )
    @transaction.atomic
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

    @extend_schema(
        summary="Actualizar Socio",
        request=ActualizarSocioSerializer,
        responses={200: SocioSerializer()}
    )
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

    @extend_schema(summary="Eliminar Socio")
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

    @action(detail=True, methods=['get'], url_path='estado-cuenta')
    @extend_schema(
        summary="Estado de Cuenta 360",
        description="Retorna propiedades, deudas, multas e historial del socio.",
        responses={200: EstadoCuentaSerializer()}
    )
    def estado_cuenta(self, request, pk=None):
        """
        Retorna el Estado de Cuenta 360° (Propiedades, Deudas, Multas, Historial).
        """
        # --- SEGURIDAD: CONTROL DE ACCESO (DATA LEAKAGE PREVENTION) ---
        if not request.user.is_staff:
            # Si no es admin/staff, debe ser el dueño de la cuenta
            # Asumimos que request.user tiene perfil_socio (OneToOne)
            if not hasattr(request.user, 'perfil_socio'):
                return Response({"error": "Usuario no vinculado a un socio"}, status=status.HTTP_403_FORBIDDEN)
            
            if request.user.perfil_socio.id != int(pk):
                return Response({"error": "No tiene permiso para ver esta cuenta"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # 1. Inicializar Repositorios
            socio_repo = DjangoSocioRepository()
            terreno_repo = DjangoTerrenoRepository()
            factura_repo = DjangoFacturaRepository()
            pago_repo = DjangoPagoRepository()
            servicio_repo = DjangoServicioRepository()

            # 2. Inicializar UseCase
            use_case = ObtenerEstadoCuentaUseCase(
                socio_repo, terreno_repo, factura_repo, pago_repo, servicio_repo
            )

            # 3. Ejecutar Lógica de Negocio
            estado_cuenta_dto = use_case.execute(int(pk))

            # 4. Serializar Respuesta
            serializer = EstadoCuentaSerializer(estado_cuenta_dto)
            
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error generando estado de cuenta: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)