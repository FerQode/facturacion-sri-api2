from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Imports de Clean Architecture
from core.use_cases.dtos import GenerarFacturaDesdeLecturaDTO
from core.use_cases.generar_factura_uc import GenerarFacturaDesdeLecturaUseCase
from core.shared.exceptions import (
    LecturaNoEncontradaError, 
    MedidorNoEncontradoError, 
    ValidacionError
)

# Adapters: Repositorios
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.repositories.django_lectura_repository import DjangoLecturaRepository
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.repositories.django_terreno_repository import DjangoTerrenoRepository

# Adapters: Servicios
from adapters.infrastructure.services.django_sri_service import DjangoSRIService

# Adapters: Serializers
from adapters.api.serializers.factura_serializers import (
    GenerarFacturaSerializer, 
    FacturaResponseSerializer,
    EnviarFacturaSRISerializer,      # Restaurado
    ConsultarAutorizacionSerializer  # Restaurado
)

# =============================================================================
# 1. GENERAR FACTURA (Lógica Principal)
# =============================================================================
class GenerarFacturaAPIView(APIView):
    """
    Endpoint para generar una factura electrónica a partir de una lectura.
    """

    @swagger_auto_schema(
        operation_description="Genera factura, calcula montos y envía al SRI.",
        request_body=GenerarFacturaSerializer,
        responses={
            201: FacturaResponseSerializer, 
            400: "Error de Validación", 
            404: "Recurso no encontrado"
        }
    )
    def post(self, request):
        # 1. Validación de Entrada
        serializer_req = GenerarFacturaSerializer(data=request.data)
        if not serializer_req.is_valid():
            return Response(serializer_req.errors, status=status.HTTP_400_BAD_REQUEST)
        
        datos_entrada = serializer_req.validated_data

        # 2. Preparar DTO
        dto = GenerarFacturaDesdeLecturaDTO(
            lectura_id=datos_entrada['lectura_id'],
            fecha_emision=datos_entrada['fecha_emision'],
            fecha_vencimiento=datos_entrada['fecha_vencimiento']
        )

        # 3. Composición de Dependencias
        factura_repo = DjangoFacturaRepository()
        lectura_repo = DjangoLecturaRepository()
        medidor_repo = DjangoMedidorRepository()
        socio_repo = DjangoSocioRepository()
        terreno_repo = DjangoTerrenoRepository()
        sri_service = DjangoSRIService() 

        # 4. Instanciar Caso de Uso
        use_case = GenerarFacturaDesdeLecturaUseCase(
            factura_repo=factura_repo,
            lectura_repo=lectura_repo,
            medidor_repo=medidor_repo,
            terreno_repo=terreno_repo,
            socio_repo=socio_repo,
            sri_service=sri_service
        )

        try:
            # 5. Ejecutar Lógica
            factura_generada = use_case.execute(dto)

            # 6. Serializar Respuesta
            serializer_res = FacturaResponseSerializer(factura_generada)
            return Response(serializer_res.data, status=status.HTTP_201_CREATED)

        except (LecturaNoEncontradaError, MedidorNoEncontradoError) as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidacionError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"ERROR CRÍTICO EN API: {str(e)}")
            return Response(
                {"error": f"Error interno del servidor: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# 2. ENVIAR AL SRI (Endpoint Manual / Reintento)
# =============================================================================
class EnviarFacturaSRIAPIView(APIView):
    """
    Vista para re-enviar una factura al SRI si falló el envío automático inicial.
    """
    @swagger_auto_schema(
        operation_description="Reintenta el envío de una factura existente al SRI.",
        request_body=EnviarFacturaSRISerializer,
        responses={200: "Enviado", 400: "Error"}
    )
    def post(self, request):
        serializer = EnviarFacturaSRISerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        factura_id = serializer.validated_data['factura_id']
        
        # Aquí eventualmente conectarás el Caso de Uso de Reintento
        # Por ahora devolvemos un mensaje simulado para que no falle el import
        return Response({
            "mensaje": "Funcionalidad de reintento pendiente de conectar al Caso de Uso",
            "factura_id": factura_id,
            "estado_sri": "EN_PROCESO"
        }, status=status.HTTP_200_OK)


# =============================================================================
# 3. CONSULTAR AUTORIZACIÓN
# =============================================================================
class ConsultarAutorizacionAPIView(APIView):
    """
    Consulta el estado de una autorización en el SRI mediante la Clave de Acceso.
    """
    @swagger_auto_schema(
        query_serializer=ConsultarAutorizacionSerializer,
        responses={200: "Estado obtenido"}
    )
    def get(self, request):
        serializer = ConsultarAutorizacionSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        clave = serializer.validated_data['clave_acceso']
        
        # Instancia del servicio real
        try:
            sri_service = DjangoSRIService()
            respuesta = sri_service.consultar_autorizacion(clave)
            
            return Response({
                "clave_acceso": clave,
                "estado": respuesta.estado,
                "mensaje": respuesta.mensaje_error or "Autorizado exitosamente",
                "xml_respuesta": respuesta.xml_respuesta
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 4. MIS FACTURAS (Historial)
# =============================================================================
class MisFacturasAPIView(APIView):
    permission_classes = [IsAuthenticated] 

    @swagger_auto_schema(responses={200: "Lista de facturas"})
    def get(self, request):
        # Esta vista sigue siendo un Mock hasta que conectes el repositorio de usuario
        return Response({
            "mensaje": "Historial de facturas (Pendiente de implementación final)",
            "usuario": request.user.username,
            "facturas": []
        }, status=status.HTTP_200_OK)