# adapters/api/views/factura_views.py

from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction 

# --- Clean Architecture: Casos de Uso y DTOs ---
from core.use_cases.dtos import GenerarFacturaDesdeLecturaDTO
from core.use_cases.generar_factura_uc import GenerarFacturaDesdeLecturaUseCase
from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase
from core.use_cases.generar_factura_fija_uc import GenerarFacturaFijaUseCase 
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

# --- Adapters: Modelos ---
# ✅ MODIFICADO: Agregamos FacturaModel para consultar deudas directas
from adapters.infrastructure.models import LecturaModel, FacturaModel

# --- Adapters: Servicios ---
from adapters.infrastructure.services.django_sri_service import DjangoSRIService

# --- Adapters: Serializers ---
from adapters.api.serializers.factura_serializers import (
    GenerarFacturaSerializer, 
    FacturaResponseSerializer,
    EnviarFacturaSRISerializer,
    ConsultarAutorizacionSerializer,
    EmisionMasivaSerializer,
    RegistrarCobroSerializer,
    LecturaPendienteSerializer 
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
        serializer_req = GenerarFacturaSerializer(data=request.data)
        if not serializer_req.is_valid():
            return Response(serializer_req.errors, status=status.HTTP_400_BAD_REQUEST)
        
        datos_entrada = serializer_req.validated_data

        dto = GenerarFacturaDesdeLecturaDTO(
            lectura_id=datos_entrada['lectura_id'],
            fecha_emision=datos_entrada['fecha_emision'],
            fecha_vencimiento=datos_entrada['fecha_vencimiento']
        )

        factura_repo = DjangoFacturaRepository()
        lectura_repo = DjangoLecturaRepository()
        medidor_repo = DjangoMedidorRepository()
        socio_repo = DjangoSocioRepository()
        terreno_repo = DjangoTerrenoRepository()
        sri_service = DjangoSRIService() 

        use_case = GenerarFacturaDesdeLecturaUseCase(
            factura_repo=factura_repo,
            lectura_repo=lectura_repo,
            medidor_repo=medidor_repo,
            terreno_repo=terreno_repo,
            socio_repo=socio_repo,
            sri_service=sri_service
        )

        try:
            factura_generada = use_case.execute(dto)
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
# 1.1 GENERACIÓN DE FACTURAS TARIFA FIJA (Sin Medidor)
# =============================================================================
class GenerarFacturasFijasAPIView(APIView):
    """
    Endpoint para ejecutar el proceso masivo de facturación para socios SIN medidor.
    Ideal para ejecutar al inicio de cada mes.
    """
    
    @swagger_auto_schema(
        operation_description="Genera facturas masivas para todos los servicios de tipo FIJO activos.",
        responses={
            200: "Reporte de ejecución (creadas, omitidas, errores)",
            500: "Error interno"
        }
    )
    def post(self, request):
        try:
            uc = GenerarFacturaFijaUseCase()
            reporte = uc.ejecutar()
            return Response(reporte, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error en generación masiva: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =============================================================================
# 2. GESTIÓN MASIVA Y COBROS (ENDPOINT INTELIGENTE)
# =============================================================================
class FacturaMasivaViewSet(viewsets.ViewSet):
    """
    Controlador para Gestión de Deudas (Cajero) y Emisión Masiva (Admin).
    """

    @swagger_auto_schema(
        operation_description="Endpoint Híbrido: Busca deudas por Cédula (Historial) O por Fecha (Reporte Mes).",
        manual_parameters=[
            openapi.Parameter('cedula', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Opcional: Filtra historial de un socio"),
            openapi.Parameter('mes', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Opcional: Filtra por mes (requiere anio)"),
            openapi.Parameter('anio', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Opcional: Filtra por año"),
        ],
        responses={200: "Lista de facturas pendientes"}
    )
    # ✅ MODIFICADO: Implementación del Endpoint Inteligente
    @action(detail=False, methods=['get'], url_path='pendientes')
    def pendientes(self, request):
        """
        Endpoint Inteligente para Cajeros y Administradores:
        1. ?cedula=XYZ -> Muestra TODO lo que debe esa persona (Enero, Febrero, etc.)
        2. ?mes=1&anio=2026 -> Muestra TODOS los socios que deben de ese mes.
        """
        cedula = request.query_params.get('cedula')
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')

        # Base: Solo buscamos facturas que no han sido pagadas
        # Usamos select_related para traer datos del socio en una sola consulta (Optimización)
        queryset = FacturaModel.objects.select_related('socio').filter(estado='PENDIENTE')

        # --- LÓGICA HÍBRIDA ---
        
        # CASO 1: Búsqueda por Socio (Prioridad Cajero)
        if cedula:
            queryset = queryset.filter(socio__cedula=cedula)
            
            # Si consultan una cédula específica y no hay deudas, respondemos bonito
            if not queryset.exists():
                return Response({
                    "mensaje": f"El socio con cédula {cedula} no tiene deudas pendientes. ¡Está al día! 🎉",
                    "data": []
                }, status=200)

        # CASO 2: Reporte General por Fecha (Admin)
        elif mes and anio:
            queryset = queryset.filter(
                fecha_emision__month=mes, 
                fecha_emision__year=anio
            )
        
        # CASO 3: Error (No envió parámetros)
        else:
            return Response({
                "error": "Parámetros insuficientes. Envíe '?cedula=...' para cobrar a un socio, O '?mes=..&anio=..' para ver pendientes del mes."
            }, status=400)

        # --- SERIALIZACIÓN MANUAL (Ligera para listas grandes) ---
        data = []
        for f in queryset:
            data.append({
                "factura_id": f.id,
                "socio": f.socio.nombres + " " + f.socio.apellidos,
                "cedula": f.socio.cedula,
                "fecha_emision": f.fecha_emision.strftime('%Y-%m-%d'),
                "total": str(f.total),
                "estado_sri": f.estado_sri, # Útil para saber si ya fue autorizado
                "estado_pago": f.estado
            })

        return Response(data, status=200)


    @swagger_auto_schema(request_body=EmisionMasivaSerializer)
    @action(detail=False, methods=['post'], url_path='emision-masiva')
    def emision_masiva(self, request):
        """
        Inicia el proceso de generar todas las facturas del mes.
        """
        serializer = EmisionMasivaSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=400)
             
        return Response({
            "mensaje": f"Proceso de emisión masiva iniciado para {serializer.validated_data['mes']}/{serializer.validated_data['anio']}",
            "estado": "PROCESANDO"
        }, status=200)


# =============================================================================
# 3. GESTIÓN DE COBROS Y PAGOS
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