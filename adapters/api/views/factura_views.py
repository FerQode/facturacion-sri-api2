import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# --- MEJORA DE BUENA PRÁCTICA (Seguridad) ---
# Importamos los permisos de DRF.
# IsAuthenticated: Solo permite usuarios con un Token JWT válido.
# IsAdminUser: Solo permite usuarios con `is_staff=True` (Admin, Tesorero).
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# --- 1. Serializers ("Porteros") ---
from adapters.api.serializers.factura_serializers import (
    GenerarFacturaSerializer,
    EnviarFacturaSRISerializer,
    ConsultarAutorizacionSerializer # <-- Import nuevo
)

# --- 2. Casos de Uso ("Cerebros") y DTOs ---
# (Usamos las nuevas rutas del refactor)
from core.use_cases.factura_uc import (
    GenerarFacturaDesdeLecturaUseCase,
    EnviarFacturaSRIUseCase,        # <-- Import que ya tenías
    ConsultarAutorizacionUseCase # <-- Import nuevo
)
from core.use_cases.factura_dtos import (
    GenerarFacturaDesdeLecturaDTO,
    EnviarFacturaSRIDTO,            # <-- Import que ya tenías
    ConsultarAutorizacionDTO # <-- Import nuevo
)

# --- 3. Repositorios y Servicios ("Traductores") ---
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.repositories.django_lectura_repository import DjangoLecturaRepository
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.services.django_sri_service import DjangoSRIService 

# --- 4. Excepciones de Negocio ---
from core.shared.exceptions import (
    LecturaNoEncontradaError, 
    MedidorNoEncontradoError, 
    SocioNoEncontradoError,
    FacturaNoEncontradaError, # <-- Import nuevo
    FacturaEstadoError        # <-- Import que ya tenías
)

# Configura un logger
logger = logging.getLogger(__name__)

# --- Vista 1: Generar Factura ---
class GenerarFacturaAPIView(APIView):
    """
    Endpoint (Ventanilla) de API para generar una nueva factura
    a partir de una lectura de consumo ya registrada.
    """
    # --- MEJORA DE BUENA PRÁCTICA (Seguridad) ---
    # Solo usuarios autenticados (Admin, Tesorero, Operador) pueden generar facturas.
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = GenerarFacturaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dto = GenerarFacturaDesdeLecturaDTO(**serializer.validated_data)
        except Exception as e:
            logger.error(f"Discrepancia entre Serializer y DTO: {e}", exc_info=True)
            return Response({"error": "Error interno de configuración."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            factura_repo = DjangoFacturaRepository()
            lectura_repo = DjangoLecturaRepository()
            medidor_repo = DjangoMedidorRepository()
            socio_repo = DjangoSocioRepository()
        except Exception as e:
            logger.error(f"Error al instanciar repositorios: {e}", exc_info=True)
            return Response({"error": "Error interno al conectar con servicios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        use_case = GenerarFacturaDesdeLecturaUseCase(
            factura_repo=factura_repo, 
            lectura_repo=lectura_repo,
            medidor_repo=medidor_repo,
            socio_repo=socio_repo
        )

        try:
            factura_creada = use_case.execute(dto)
        
        except (LecturaNoEncontradaError, MedidorNoEncontradoError, SocioNoEncontradoError) as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado en GenerarFacturaUseCase: {e}", exc_info=True)
            return Response({"error": f"Error interno del servidor: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            respuesta_data = {
                "id": factura_creada.id,
                "socio_id": factura_creada.socio_id,
                "estado": factura_creada.estado.value,
                "total": f"{factura_creada.total:.2f}",
                "detalles": [d.concepto for d in factura_creada.detalles]
            }
            return Response(respuesta_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error al serializar la respuesta: {e}", exc_info=True)
            return Response({"error": "Factura creada pero hubo un error al formatear la respuesta."}, status=status.HTTP_201_CREATED)

# --- Vista 2: Enviar Factura al SRI ---
class EnviarFacturaSRIAPIView(APIView):
    """
    Endpoint (Ventanilla) de API para enviar una factura existente
    al Servicio de Rentas Internas (SRI) para su autorización.
    """
    # --- MEJORA DE BUENA PRÁCTICA (Seguridad) ---
    # Solo usuarios autenticados (Admin, Tesorero) pueden enviar al SRI.
    # Usamos IsAdminUser, que verifica que request.user.is_staff == True.
    permission_classes = [IsAdminUser]
    
    def post(self, request, *args, **kwargs):
        
        serializer = EnviarFacturaSRISerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dto = EnviarFacturaSRIDTO(**serializer.validated_data)
        except Exception as e:
             logger.error(f"Discrepancia entre Serializer y DTO (EnviarSRI): {e}", exc_info=True)
             return Response({"error": "Error interno de configuración."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            factura_repo = DjangoFacturaRepository()
            socio_repo = DjangoSocioRepository()
            sri_service = DjangoSRIService()
        except Exception as e:
            logger.error(f"Error al instanciar servicios/repos: {e}", exc_info=True)
            return Response({"error": "Error interno al conectar con servicios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        use_case = EnviarFacturaSRIUseCase(
            factura_repo=factura_repo, 
            socio_repo=socio_repo,
            sri_service=sri_service
        )

        try:
            sri_response = use_case.execute(dto)
        
        except FacturaNoEncontradaError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except FacturaEstadoError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado en EnviarFacturaSRIUseCase: {e}", exc_info=True)
            return Response({"error": f"Error interno del servidor: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        respuesta_data = {
            "exito_sri": sri_response.exito,
            "estado_sri": sri_response.estado,
            "clave_acceso": sri_response.autorizacion_id,
            "mensaje": sri_response.mensaje_error
        }
        
        return Response(respuesta_data, status=status.HTTP_200_OK)

# --- PASO 5: Vista NUEVA A AÑADIR ---
class ConsultarAutorizacionAPIView(APIView):
    """
    Endpoint (Ventanilla) para consultar el estado de autorización
    de una factura ya enviada al SRI.
    """
    # --- MEJORA DE BUENA PRÁCTICA (Seguridad) ---
    # Permitimos que cualquier usuario autenticado (incluido un "Socio")
    # pueda consultar el estado de una factura.
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Maneja la petición POST a /api/v1/facturas/consultar/
        """
        
        # 1. Validar la entrada con el "Portero"
        serializer = ConsultarAutorizacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Convertir a DTO
        try:
            dto = ConsultarAutorizacionDTO(**serializer.validated_data)
        except Exception as e:
            logger.error(f"Discrepancia entre Serializer y DTO: {e}", exc_info=True)
            return Response({"error": "Error interno de configuración."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # 3. Ensamblar "Herramientas"
        try:
            factura_repo = DjangoFacturaRepository()
            sri_service = DjangoSRIService()
        except Exception as e:
            logger.error(f"Error al instanciar servicios: {e}", exc_info=True)
            return Response({"error": "Error interno al conectar con servicios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 4. Instanciar "Cerebro"
        use_case = ConsultarAutorizacionUseCase(
            factura_repo=factura_repo, 
            sri_service=sri_service
        )
        
        # 5. Ejecutar lógica
        try:
            sri_response = use_case.execute(dto)
        
        # 6. Manejar errores de negocio
        except FacturaNoEncontradaError as e:
             return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado en ConsultarAutorizacionUseCase: {e}", exc_info=True)
            return Response({"error": f"Error interno del servidor: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 7. Devolver respuesta exitosa (del SRI)
        respuesta_data = {
            "exito_sri": sri_response.exito,
            "estado_sri": sri_response.estado,
            "clave_acceso": sri_response.autorizacion_id,
            "mensaje": sri_response.mensaje_error
        }
        
        return Response(respuesta_data, status=status.HTTP_200_OK)
