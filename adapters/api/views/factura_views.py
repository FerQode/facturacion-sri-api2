# adapters/api/views/factura_views.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# --- 1. El "Portero" (Serializer) ---
from adapters.api.serializers.factura_serializers import GenerarFacturaSerializer
from adapters.api.serializers.factura_serializers import EnviarFacturaSRISerializer

# --- 2. El "Cerebro" (Use Case) y su DTO ---
from core.use_cases.generar_factura_uc import GenerarFacturaDesdeLecturaUseCase
from core.use_cases.dtos import GenerarFacturaDesdeLecturaDTO
from core.use_cases.enviar_factura_sri_uc import EnviarFacturaSRIUseCase

# --- 3. Los "Traductores" (Implementaciones de Repositorios) ---
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.repositories.django_lectura_repository import DjangoLecturaRepository
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.services.django_sri_service import DjangoSRIService

# --- 4. Las "Excepciones de Negocio" (Errores que el "Cerebro" puede lanzar) ---
from core.shared.exceptions import LecturaNoEncontradaError, MedidorNoEncontradoError, SocioNoEncontradoError
from core.shared.exceptions import FacturaNoEncontradaError, FacturaEstadoError

# Configura un logger para registrar errores inesperados
logger = logging.getLogger(__name__)

class GenerarFacturaAPIView(APIView):
    """
    Endpoint (Ventanilla) de API para generar una nueva factura
    a partir de una lectura de consumo ya registrada.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Maneja la petición POST a /api/v1/facturas/generar/
        """
        
        # --- PASO 1: Validar la entrada con el "Portero" ---
        serializer = GenerarFacturaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # --- PASO 2: Convertir datos validados al DTO que el "Cerebro" espera ---
        try:
            dto = GenerarFacturaDesdeLecturaDTO(**serializer.validated_data)
        except Exception as e:
            # Esto podría pasar si el DTO y el Serializer no coinciden
            logger.error(f"Discrepancia entre Serializer y DTO: {e}", exc_info=True)
            return Response({"error": "Error interno de configuración."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- PASO 3: Ensamblar las "Herramientas" (Inyección de Dependencias) ---
        # La Vista es la única que sabe qué implementaciones concretas usar.
        try:
            factura_repo = DjangoFacturaRepository()
            lectura_repo = DjangoLecturaRepository()
            medidor_repo = DjangoMedidorRepository()
            socio_repo = DjangoSocioRepository()
        except Exception as e:
            logger.error(f"Error al instanciar repositorios: {e}", exc_info=True)
            return Response({"error": "Error interno al conectar con servicios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        # --- PASO 4: Instanciar el "Cerebro" (Use Case) e inyectar las herramientas ---
        use_case = GenerarFacturaDesdeLecturaUseCase(
            factura_repo=factura_repo, 
            lectura_repo=lectura_repo,
            medidor_repo=medidor_repo,
            socio_repo=socio_repo
        )

        # --- PASO 5: Ejecutar la lógica de negocio ---
        try:
            factura_creada = use_case.execute(dto)
        
        # --- PASO 6A: Manejar Errores de Negocio (esperados) ---
        # Atrapamos las excepciones personalizadas que el "Cerebro" lanza.
        except (LecturaNoEncontradaError, MedidorNoEncontradoError, SocioNoEncontradoError) as e:
            # Errores "Not Found" (404)
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Errores inesperados (500)
            logger.error(f"Error inesperado en GenerarFacturaUseCase: {e}", exc_info=True)
            return Response({"error": f"Error interno del servidor: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- PASO 6B: Formatear y devolver la respuesta de ÉXITO ---
        # Traducimos la Entidad (lógica pura) a un JSON simple.
        try:
            respuesta_data = {
                "id": factura_creada.id,
                "socio_id": factura_creada.socio_id,
                "estado": factura_creada.estado.value, # "Pendiente"
                "total": f"{factura_creada.total:.2f}", # Formateado como string
                "detalles": [d.concepto for d in factura_creada.detalles]
            }
            return Response(respuesta_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error al serializar la respuesta: {e}", exc_info=True)
            return Response({"error": "Factura creada pero hubo un error al formatear la respuesta."}, status=status.HTTP_201_CREATED)
        
class EnviarFacturaSRIAPIView(APIView):
    """
    Endpoint (Ventanilla) de API para enviar una factura existente
    al Servicio de Rentas Internas (SRI) para su autorización.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Maneja la petición POST a /api/v1/facturas/enviar-sri/
        """
        
        # --- PASO 1: Validar la entrada con el "Portero" ---
        serializer = EnviarFacturaSRISerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        factura_id = serializer.validated_data['factura_id']

        # --- PASO 2: Ensamblar las "Herramientas" (Inyección de Dependencias) ---
        # Este Caso de Uso necesita los repositorios Y el servicio del SRI.
        try:
            factura_repo = DjangoFacturaRepository()
            socio_repo = DjangoSocioRepository()
            # ¡Aquí instanciamos el adaptador del SRI!
            sri_service = DjangoSRIService()
        except Exception as e:
            logger.error(f"Error al instanciar servicios/repos: {e}", exc_info=True)
            return Response({"error": "Error interno al conectar con servicios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        # --- PASO 3: Instanciar el "Cerebro" (Use Case) e inyectar las herramientas ---
        use_case = EnviarFacturaSRIUseCase(
            factura_repo=factura_repo, 
            socio_repo=socio_repo,
            sri_service=sri_service
        )

        # --- PASO 4: Ejecutar la lógica de negocio ---
        try:
            # El "cerebro" hace todo: busca, genera XML, firma, envía y actualiza.
            sri_response = use_case.execute(factura_id)
        
        # --- PASO 5A: Manejar Errores de Negocio (esperados) ---
        except FacturaNoEncontradaError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except FacturaEstadoError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado en EnviarFacturaSRIUseCase: {e}", exc_info=True)
            return Response({"error": f"Error interno del servidor: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- PASO 5B: Formatear y devolver la respuesta de ÉXITO ---
        # Devolvemos la respuesta directa del servicio SRI (éxito o error de SRI)
        respuesta_data = {
            "exito_sri": sri_response.exito,
            "estado_sri": sri_response.estado,
            "clave_acceso": sri_response.autorizacion_id,
            "mensaje": sri_response.mensaje_error
        }
        
        # Si el SRI aceptó la factura (RECIBIDA) o la rechazó (DEVUELTA),
        # la operación de nuestra API fue exitosa.
        return Response(respuesta_data, status=status.HTTP_200_OK)