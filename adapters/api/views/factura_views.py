# adapters/api/views/factura_views.py

from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import date
from django.db import transaction

# --- Clean Architecture: Casos de Uso y DTOs ---
from core.use_cases.dtos import GenerarFacturaDesdeLecturaDTO
from core.use_cases.generar_factura_uc import GenerarFacturaDesdeLecturaUseCase
from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase
from core.use_cases.generar_factura_fija_uc import GenerarFacturaFijaUseCase
from core.services.facturacion_service import FacturacionService
from core.use_cases.generar_factura_fija_uc import GenerarFacturaFijaUseCase
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
from adapters.infrastructure.repositories.django_servicio_repository import DjangoServicioRepository # ✅ NEW

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
    permission_classes = [IsAuthenticated, IsAdminUser]

    @swagger_auto_schema(
        operation_description="Genera facturas masivas para todos los servicios de tipo FIJO activos.",
        responses={
            200: "Reporte de ejecución (creadas, omitidas, errores)",
            500: "Error interno"
        }
    )
    def post(self, request):
        try:
            # ✅ Clean Architecture: Inyección de Dependencias Manual
            factura_repo = DjangoFacturaRepository()
            servicio_repo = DjangoServicioRepository()
            
            # Capturar parametros del body (Periodo Fiscal y Fecha Emision)
            anio = request.data.get('anio')
            mes = request.data.get('mes')
            
            # Fecha de Emision Legal (Opcional, por defecto hoy)
            # Puede ser distinto al periodo fiscal (Ej: Facturo Diciembre en Enero)
            fecha_emision_str = request.data.get('fecha_emision')
            fecha_emision = date.fromisoformat(fecha_emision_str) if fecha_emision_str else None

            uc = GenerarFacturaFijaUseCase(
                factura_repo=factura_repo,
                servicio_repo=servicio_repo
            )
            
            reporte = uc.ejecutar(anio=anio, mes=mes, fecha_emision=fecha_emision)
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
# ======================================================
    # ENDPOINT INTELIGENTE (VERSIÓN DEFINITIVA - CASCADA)
    # ======================================================
    @action(detail=False, methods=['get'], url_path='pendientes')
    def pendientes(self, request):
        """
        Endpoint Inteligente:
        Maneja Cédula, Fechas y Estado en cascada.
        """
        # 1. Capturamos TODOS los parámetros
        cedula = request.query_params.get('cedula')
        dia = request.query_params.get('dia')   # ¡Ojo! Agregué 'dia' porque vi en tu log que lo envías
        mes = request.query_params.get('mes')
        anio = request.query_params.get('anio')
        ver_historial = request.query_params.get('ver_historial')

        # 2. Query Base
        queryset = FacturaModel.objects.select_related(
            'socio', 'medidor', 'lectura'
        ).order_by('-fecha_emision')

        # -----------------------------------------------------
        # FASE 1: FILTROS DE BÚSQUEDA (Se suman, no se excluyen)
        # -----------------------------------------------------

        # Filtro por Socio
        if cedula:
            queryset = queryset.filter(socio__cedula__icontains=cedula) # icontains es más flexible

        # Filtro por Fecha (Puede combinarse con cédula o ir solo)
        if anio:
            queryset = queryset.filter(fecha_emision__year=anio)
        if mes:
            queryset = queryset.filter(fecha_emision__month=mes)
        if dia:
            queryset = queryset.filter(fecha_emision__day=dia)

        # -----------------------------------------------------
        # FASE 2: LA REGLA DE ORO (Estado)
        # -----------------------------------------------------

        # Si NO piden explícitamente ver el historial...
        # ...ENTONCES SOLO MOSTRAMOS LO QUE SE DEBE (PENDIENTE)
        if ver_historial != 'true':
            queryset = queryset.filter(estado__in=['PENDIENTE', 'POR_VALIDAR'])

        # Si piden historial (ver_historial='true'), no filtramos estado
        # y mostramos todo (Pagadas + Pendientes).

        # Validación si no hay resultados
        if not queryset.exists():
            return Response([], status=200)

        # -----------------------------------------------------
        # FASE 3: SERIALIZACIÓN
        # -----------------------------------------------------
        data = []
        for f in queryset:
            codigo_medidor = "SIN MEDIDOR"
            consumo_str = "-"

            if f.medidor:
                codigo_medidor = f.medidor.codigo

            if f.lectura:
                consumo_str = f"{f.lectura.consumo_del_mes}"

            clave_sri = getattr(f, 'clave_acceso', None) or getattr(f, 'clave_acceso_sri', None)

            data.append({
                "factura_id": f.id,
                "socio": f.socio.nombres + " " + f.socio.apellidos,
                "cedula": f.socio.cedula,
                "fecha_emision": f.fecha_emision.strftime('%Y-%m-%d'),
                "medidor": codigo_medidor,
                "consumo": consumo_str,
                "agua": str(f.subtotal),
                "multas": "0.00",
                "total": str(f.total),
                "estado_sri": f.estado_sri,
                "estado_pago": f.estado,
                "direccion": f.socio.direccion or "S/N",
                "clave_acceso_sri": clave_sri
            })

        return Response(data, status=200)


# ======================================================
    # EMISIÓN MASIVA (LÓGICA REAL QUE CAMBIA EL 0 A 1)
    # ======================================================
    @swagger_auto_schema(request_body=EmisionMasivaSerializer)
    @action(detail=False, methods=['post'], url_path='emision-masiva')
    def emision_masiva(self, request):
        """
        Ejecuta la facturación REAL:
        1. Procesa lecturas pendientes (Edison).
        2. Procesa tarifas fijas (Adrián).
        """
        serializer = EmisionMasivaSerializer(data=request.data)
        if not serializer.is_valid():
             return Response(serializer.errors, status=400)

        mes = serializer.validated_data['mes']
        anio = serializer.validated_data['anio']

        # TRANSACCIÓN ATÓMICA: Todo o Nada (Seguridad Bancaria)
        with transaction.atomic():

            # --- PASO A: FACTURAR MEDIDORES (EDISON) ---
            # Buscamos lecturas que existen PERO no se han cobrado (esta_facturada=0)
            lecturas_pendientes = LecturaModel.objects.filter(
                esta_facturada=False,   # <--- Aquí buscamos los ceros
                fecha__month=mes,
                fecha__year=anio,
                medidor__estado='ACTIVO'
            )

            medidores_procesados = 0
            errores_medidores = []

            # Inicializamos repositorios
            factura_repo = DjangoFacturaRepository()
            lectura_repo = DjangoLecturaRepository()
            medidor_repo = DjangoMedidorRepository()
            socio_repo = DjangoSocioRepository()
            terreno_repo = DjangoTerrenoRepository()
            sri_service = DjangoSRIService()

            use_case_medidor = GenerarFacturaDesdeLecturaUseCase(
                factura_repo, lectura_repo, medidor_repo,
                terreno_repo, socio_repo
            )

            # Procesamos a Edison y compañía
            for lect in lecturas_pendientes:
                try:
                    dto = GenerarFacturaDesdeLecturaDTO(
                        lectura_id=lect.id,
                        fecha_emision=date.today(),
                        fecha_vencimiento=date.today()
                    )
                    use_case_medidor.execute(dto)
                    # NOTA: El use_case internamente pone lect.esta_facturada = True (1)
                    medidores_procesados += 1
                except Exception as e:
                    errores_medidores.append(f"Lectura ID {lect.id}: {str(e)}")

            # --- PASO B: FACTURAR ACOMETIDAS FIJAS (ADRIÁN) ---
            # Esto busca socios SIN medidor y les cobra los $3.00
            
            # ✅ Clean Architecture: Inyección para Masiva también
            servicio_repo = DjangoServicioRepository() # factura_repo ya existe arriba
            
            uc_fija = GenerarFacturaFijaUseCase(
                factura_repo=factura_repo,
                servicio_repo=servicio_repo
            )
            reporte_fijas = uc_fija.ejecutar()

        # --- RESPUESTA ---
        return Response({
            "mensaje": "Proceso de emisión finalizado exitosamente.",
            "resumen": {
                "medidores_generados": medidores_procesados,
                "acometidas_generadas": reporte_fijas.get('creadas', 0),
                "errores": errores_medidores + reporte_fijas.get('errores', []),
                "mes_procesado": f"{mes}/{anio}"
            }
        }, status=200)

# ======================================================
    # NUEVO: PRE-VISUALIZACIÓN (CORREGIDO - NORMATIVA REAL)
    # ======================================================
    @action(detail=False, methods=['get'], url_path='pre-emision')
    def pre_emision(self, request):
        """
        Devuelve la lista de Lecturas listas para cobrar.
        """
        # 1. Buscamos lecturas NO facturadas
        lecturas_pendientes = LecturaModel.objects.select_related(
            'medidor', 'medidor__terreno__socio'
        ).filter(
            esta_facturada=False,
            medidor__estado='ACTIVO'
        ).order_by('medidor__terreno__socio__apellidos')

        data = []

        # --- VALORES SEGÚN RESOLUCIÓN MAATE ---
        TARIFA_BASE = 3.00
        VALOR_M3_EXTRA = 0.25
        BASE_M3 = 120

        for lect in lecturas_pendientes:
            consumo = float(lect.consumo_del_mes)

            valor_estimado = TARIFA_BASE

            # Solo cobramos extra si supera los 120 metros cúbicos
            if consumo > BASE_M3:
                excedente = consumo - BASE_M3
                valor_estimado += (excedente * VALOR_M3_EXTRA)

            nombre_socio = "Desconocido"
            if lect.medidor and lect.medidor.terreno and lect.medidor.terreno.socio:
                nombre_socio = f"{lect.medidor.terreno.socio.apellidos} {lect.medidor.terreno.socio.nombres}"

            data.append({
                "lectura_id": lect.id,
                "socio": nombre_socio,
                "codigo_medidor": lect.medidor.codigo,
                "lectura_anterior": lect.lectura_anterior,
                "lectura_actual": lect.valor,
                "consumo": consumo,
                "valor_estimado": round(valor_estimado, 2),
                "estado": "LISTO PARA FACTURAR"
            })

        return Response(data, status=status.HTTP_200_OK)
# =============================================================================
# 3. GESTIÓN DE COBROS Y PAGOS
# =============================================================================
class CobroViewSet(viewsets.ViewSet):

    # ✅ AGREGA ESTO: Define que la URL será /api/v1/cobros/registrar/
    @action(detail=False, methods=['post'], url_path='registrar')
    def registrar_cobro(self, request):
        serializer = RegistrarCobroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ IMPORTANTE: Inyectar repositorios si el caso de uso los requiere
            # Si tu RegistrarCobroUseCase() no tiene constructor, déjalo así,
            # pero usualmente se inyectan como los otros.
            uc = RegistrarCobroUseCase()

            resultado = uc.ejecutar(
                factura_id=serializer.validated_data['factura_id'],
                lista_pagos=serializer.validated_data['pagos']
            )
            return Response(resultado, status=status.HTTP_200_OK)

        except (EntityNotFoundException, BusinessRuleException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    Consulta el estado en el SRI y ACTUALIZA la base de datos local.
    Ideal para resolver estados 'EN PROCESAMIENTO' o 'PENDIENTE'.
    """
    @swagger_auto_schema(
        operation_description="Consulta SRI por clave de acceso y sincroniza el estado local.",
        query_serializer=ConsultarAutorizacionSerializer,
        responses={200: "Estado sincronizado"}
    )
    def get(self, request):
        serializer = ConsultarAutorizacionSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        clave = serializer.validated_data['clave_acceso']

        try:
            sri_service = DjangoSRIService()
            # 1. Llamada real al SOAP del SRI
            respuesta = sri_service.consultar_autorizacion(clave)
# --- AGREGA ESTA LÍNEA PARA VER EL MENSAJE EN LA TERMINAL ---
            print(f"DEBUG SRI RESPUESTA: {respuesta.estado} - {respuesta.mensaje_error}")
        # ------------------------------------------------------------
            # 2. Si el SRI dice que ya está AUTORIZADO, actualizamos nuestra BD
            if respuesta.estado == "AUTORIZADO":
                # Buscamos la factura que tiene esa clave
                factura_db = FacturaModel.objects.filter(clave_acceso_sri=clave).first()
                if factura_db:
                    factura_db.estado_sri = "AUTORIZADO"
                    factura_db.xml_autorizado_sri = respuesta.xml_respuesta
                    # Si ya está autorizado, nos aseguramos que el pago esté en firme
                    factura_db.estado = "PAGADA"
                    factura_db.save()

            return Response({
                "clave_acceso": clave,
                "estado": respuesta.estado,
                "mensaje": "Estado actualizado en el sistema" if respuesta.exito else "El SRI aún no autoriza el documento.",
                "detalles": respuesta.mensaje_error,
                "xml_respuesta": respuesta.xml_respuesta if respuesta.exito else None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Error de conexión con SRI: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MisFacturasAPIView(APIView):
    """
    Endpoint para que el socio logueado consulte su propio historial.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retorna el historial de facturas del socio autenticado.",
        responses={200: "Lista de facturas con detalles de consumo"}
    )
    def get(self, request):
        try:
            # 1. Buscamos las facturas asociadas a la cédula del usuario logueado
            # Nota: Usamos select_related para traer los datos del medidor y lectura en una sola consulta
            facturas_queryset = FacturaModel.objects.select_related(
                'socio', 'medidor', 'lectura'
            ).filter(
                socio__cedula=request.user.username  # Asumiendo que el username es la cédula
            ).order_by('-fecha_emision')

            # 2. Construimos la respuesta manual compatible con el map de tu Angular
            data = []
            for f in facturas_queryset:
                # Lógica para el detalle de consumo
                detalle_obj = None
                if f.lectura:
                    detalle_obj = {
                        "lectura_anterior": float(f.lectura.lectura_anterior),
                        "lectura_actual": float(f.lectura.valor),
                        "consumo_total": float(f.lectura.consumo_del_mes),
                        "costo_base": 3.00  # O la lógica de costo que manejes
                    }

                data.append({
                    "id": f.id,
                    "fecha_emision": f.fecha_emision.strftime('%Y-%m-%d'),
                    "fecha_vencimiento": f.fecha_vencimiento.strftime('%Y-%m-%d'),
                    "total": str(f.total),
                    "estado": f.estado,
                    "clave_acceso_sri": f.clave_acceso_sri,
                    "socio": {
                        "nombres": f.socio.nombres,
                        "apellidos": f.socio.apellidos,
                        "cedula": f.socio.cedula,
                        "direccion": f.socio.direccion
                    },
                    "detalle": detalle_obj
                })

            return Response({
                "mensaje": "Historial recuperado",
                "usuario": request.user.username,
                "facturas": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"Error al recuperar historial: {str(e)}",
                "facturas": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)