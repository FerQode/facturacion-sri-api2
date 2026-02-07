# adapters/api/views/cobro_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db import transaction

# Imports del Dominio
from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase
from core.shared.enums import MetodoPagoEnum, EstadoFactura
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

# Modelos (Para lectura/validación)
from adapters.infrastructure.models.factura_model import FacturaModel
from adapters.infrastructure.models.pago_model import PagoModel

# Implementaciones Concretas (Infraestructura)
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.repositories.django_pago_repository import DjangoPagoRepository
from adapters.infrastructure.services.django_sri_service import DjangoSRIService
from adapters.infrastructure.services.django_email_service import DjangoEmailService

# ✅ IMPORTAMOS LOS SERIALIZERS (Asegúrate de que la ruta sea correcta)
from adapters.api.serializers.factura_serializers import (
    RegistrarCobroSerializer,
    ReportarPagoSerializer,
    ValidarPagoSerializer
)

class CobroViewSet(viewsets.ViewSet):
    """
    Controlador de Recaudación.
    """

    # --------------------------------------------------------------------------
    # 1. COBRO EN VENTANILLA (Tesorero)
    # --------------------------------------------------------------------------
    @extend_schema(request=RegistrarCobroSerializer)
    @action(detail=False, methods=['post'], url_path='registrar')
    @transaction.atomic # ✅ Transacción controlada en el Entry Point
    def registrar_cobro(self, request):
        serializer = RegistrarCobroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # INYECCIÓN DE DEPENDENCIAS MANUAL (Wiring)
            # En un proyecto más grande usaríamos un contenedor IoC
            factura_repo = DjangoFacturaRepository()
            pago_repo = DjangoPagoRepository()
            sri_service = DjangoSRIService()
            email_service = DjangoEmailService()

            uc = RegistrarCobroUseCase(
                factura_repo=factura_repo,
                pago_repo=pago_repo,
                sri_service=sri_service,
                email_service=email_service
            )

            # Pagos directos en ventanilla nacen validados
            resultado = uc.ejecutar(
                factura_id=serializer.validated_data['factura_id'],
                lista_pagos=serializer.validated_data['pagos']
            )
            return Response(resultado, status=status.HTTP_200_OK)

        except (EntityNotFoundException, BusinessRuleException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log de error crítico
            return Response({"error": "Error interno", "detalle": str(e)}, status=500)

    # --------------------------------------------------------------------------
    # 2. SOCIO SUBE COMPROBANTE (Móvil)
    # --------------------------------------------------------------------------
    @extend_schema(request=ReportarPagoSerializer)
    @action(detail=False, methods=['post'], url_path='subir_comprobante', parser_classes=[MultiPartParser, FormParser])
    def subir_comprobante(self, request):
        serializer = ReportarPagoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            factura = FacturaModel.objects.get(pk=data['factura_id'])

            if factura.estado == EstadoFactura.PAGADA.value:
                return Response({"error": "Esta factura ya está pagada."}, status=400)

            # Guardamos el pago como NO VALIDADO
            pago = PagoModel.objects.create(
                factura=factura,
                metodo='TRANSFERENCIA',
                monto=data['monto'],
                referencia=data['referencia'],
                comprobante_imagen=data['comprobante'],
                validado=False  # ⏳ Requiere revisión del Tesorero
            )

            # Actualizamos estado de factura
            factura.estado = EstadoFactura.POR_VALIDAR.value
            factura.save()

            return Response({
                "mensaje": "Comprobante recibido. Pendiente de aprobación.",
                "pago_id": pago.id,
                "foto_url": pago.comprobante_imagen.url if pago.comprobante_imagen else None
            }, status=status.HTTP_201_CREATED)

        except FacturaModel.DoesNotExist:
            return Response({"error": "Factura no encontrada"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # --------------------------------------------------------------------------
    # 3. TESORERO VALIDA (Listar y Aprobar)
    # --------------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='pendientes-validacion')
    def listar_pendientes_validacion(self, request):
        # Traemos pagos no validados con datos del socio para mostrar en tabla
        pagos = PagoModel.objects.filter(validado=False).select_related('factura', 'factura__socio')

        data = []
        for p in pagos:
            # Construimos la URL completa de la imagen
            img_url = request.build_absolute_uri(p.comprobante_imagen.url) if p.comprobante_imagen else None

            data.append({
                "pago_id": p.id,
                "factura_id": p.factura.id,
                "socio": f"{p.factura.socio.nombres} {p.factura.socio.apellidos}",
                "cedula": p.factura.socio.cedula,
                "banco_fecha": p.fecha_registro.strftime("%Y-%m-%d %H:%M"),
                "monto": p.monto,
                "referencia": p.referencia,
                "comprobante_url": img_url
            })
        return Response(data, status=200)

    @action(detail=False, methods=['post'], url_path='validar-transferencia')
    def validar_transferencia(self, request):
        serializer = ValidarPagoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        pago_id = serializer.validated_data['pago_id']
        accion = serializer.validated_data['accion']

        try:
            pago = PagoModel.objects.get(id=pago_id)
            factura = pago.factura

            if accion == 'RECHAZAR':
                pago.delete() # O marcar como rechazado
                # Si no hay más pagos pendientes, devolvemos a PENDIENTE
                if not factura.pagos_registrados.filter(validado=False).exists():
                    factura.estado = EstadoFactura.PENDIENTE.value
                    factura.save()
                return Response({"mensaje": "Pago rechazado."}, status=200)

            elif accion == 'APROBAR':
                pago.validado = True
                pago.save()

                return Response({
                    "mensaje": "Transferencia VERIFICADA. Ya puede proceder al cobro en Caja."
                }, status=200)

        except PagoModel.DoesNotExist:
            return Response({"error": "Pago no encontrado"}, status=404)