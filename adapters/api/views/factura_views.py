# adapters/api/views/factura_views.py

from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# --- Clean Architecture: Casos de Uso y DTOs ---
from core.use_cases.dtos import GenerarFacturaDesdeLecturaDTO
from core.use_cases.generar_factura_uc import GenerarFacturaDesdeLecturaUseCase
from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase
from core.services.facturacion_service import FacturacionService

# --- Clean Architecture: Excepciones ---
from core.shared.exceptions import (
    LecturaNoEncontradaError, 
    MedidorNoEncontradoError, 
    ValidacionError,
    EntityNotFoundException,
    BusinessRuleException
)

# --- Adapters: Repositorios ---
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.repositories.django_lectura_repository import DjangoLecturaRepository
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.repositories.django_terreno_repository import DjangoTerrenoRepository
from adapters.infrastructure.repositories.django_multa_repository import DjangoMultaRepository

# --- Adapters: Modelos (Para optimización de consultas con ORM) ---
from adapters.infrastructure.models import LecturaModel

# --- Adapters: Servicios ---
from adapters.infrastructure.services.django_sri_service import DjangoSRIService

# --- Adapters: Serializers ---
from adapters.api.serializers.factura_serializers import (
    GenerarFacturaSerializer, 
    FacturaResponseSerializer,
    EnviarFacturaSRISerializer,
    ConsultarAutorizacionSerializer,
    EmisionMasivaSerializer,   # ✅ Nuevo
    RegistrarCobroSerializer   # ✅ Nuevo
)

# =============================================================================
# 1. GENERAR FACTURA INDIVIDUAL (Lógica Principal)
# =============================================================================
class GenerarFacturaAPIView(APIView):
    """
    Endpoint para generar una factura electrónica a partir de una lectura INDIVIDUAL.
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
# 2. GESTIÓN MASIVA Y PRE-VISUALIZACIÓN (NUEVO ✅)
# =============================================================================
class FacturaMasivaViewSet(viewsets.ViewSet):
    """
    Controlador para Pre-visualización de deudas (Agua + Multas) y Emisión Masiva.
    """
    
    def _get_services(self):
        return {
            "lectura_repo": DjangoLecturaRepository(),
            "socio_repo": DjangoSocioRepository(),
            "multa_repo": DjangoMultaRepository(),
            # ✅ CORRECTO: Instanciamos sin argumentos (Stateless Service)
            "billing_service": FacturacionService()
        }

    @swagger_auto_schema(
        operation_description="Devuelve la simulación de facturas (Agua + Multas) sin guardar.",
        manual_parameters=[
            openapi.Parameter('mes', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('anio', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={200: "Lista de previsualización"}
    )
    @action(detail=False, methods=['get'], url_path='pendientes')
    def previsualizar_pendientes(self, request):
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')
        
        if not mes or not anio:
            return Response({"error": "Faltan parámetros obligatorios: ?mes=12&anio=2025"}, status=400)

        services = self._get_services()
        billing_service = services['billing_service']
        
        # A. Optimización: Usamos ORM con select_related para evitar N+1
        lecturas_qs = LecturaModel.objects.select_related(
            'medidor__terreno__socio'
        ).filter(
            fecha__month=mes, 
            fecha__year=anio
            # .filter(estado='NO_FACTURADA') # Descomentar si existe estado en lectura
        )
        
        data_response = []
        
        for lectura_model in lecturas_qs:
            # B. Mapeo Rápido a Dominio (Usando el método corregido del repo)
            lectura_entity = services['lectura_repo']._map_model_to_domain(lectura_model)
            
            # Inyectamos código medidor manual (Porque el mapper base quizás no trae relaciones profundas)
            lectura_entity.medidor_codigo = lectura_model.medidor.codigo 
            
            # Obtenemos el socio desde el modelo cargado por select_related
            socio_model = lectura_model.medidor.terreno.socio
            socio_entity = services['socio_repo']._map_model_to_domain(socio_model)
            
            # C. Buscar Multas Pendientes
            multas = services['multa_repo'].obtener_pendientes_por_socio(socio_entity.id)
            
            # D. Calcular con Servicio de Dominio
            calculo = billing_service.previsualizar_factura(lectura_entity, socio_entity, multas)
            
            data_response.append(calculo)

        return Response(data_response, status=200)

    @swagger_auto_schema(request_body=EmisionMasivaSerializer)
    @action(detail=False, methods=['post'], url_path='emision-masiva')
    def emision_masiva(self, request):
        serializer = EmisionMasivaSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=400)
             
        # Aquí iría la lógica de iterar y guardar usando el Caso de Uso Masivo
        return Response({
            "mensaje": f"Proceso de emisión masiva iniciado para {serializer.validated_data['mes']}/{serializer.validated_data['anio']}",
            "estado": "PROCESANDO"
        }, status=200)


# =============================================================================
# 3. GESTIÓN DE COBROS Y PAGOS (NUEVO ✅)
# =============================================================================
class CobroViewSet(viewsets.ViewSet):
    """
    Maneja la recaudación y registro de pagos mixtos.
    """

    @swagger_auto_schema(request_body=RegistrarCobroSerializer)
    @action(detail=False, methods=['post'], url_path='registrar')
    def registrar_cobro(self, request):
        serializer = RegistrarCobroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            uc = RegistrarCobroUseCase()
            resultado = uc.ejecutar(
                factura_id=serializer.validated_data['factura_id'],
                lista_pagos=serializer.validated_data['pagos']
            )
            return Response(resultado, status=status.HTTP_200_OK)

        except (EntityNotFoundException, BusinessRuleException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# 4. UTILITARIOS SRI (Reintentos y Consultas)
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
        
        return Response({
            "mensaje": "Funcionalidad de reintento pendiente de conectar al Caso de Uso",
            "factura_id": factura_id,
            "estado_sri": "EN_PROCESO"
        }, status=status.HTTP_200_OK)


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


class MisFacturasAPIView(APIView):
    permission_classes = [IsAuthenticated] 

    @swagger_auto_schema(responses={200: "Lista de facturas"})
    def get(self, request):
        return Response({
            "mensaje": "Historial de facturas (Pendiente de implementación final)",
            "usuario": request.user.username,
            "facturas": []
        }, status=status.HTTP_200_OK)