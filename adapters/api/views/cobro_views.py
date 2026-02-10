# adapters/api/views/cobro_views.py
from rest_framework import viewsets, status, serializers, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db import transaction, models
from decimal import Decimal

# Imports del Dominio y Modelos
from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase
from core.shared.enums import MetodoPagoEnum, EstadoFactura, EstadoCuentaPorCobrar
import re
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException
from adapters.infrastructure.models import (
    FacturaModel, PagoModel, DetallePagoModel, 
    CuentaPorCobrarModel, ServicioModel
)
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.repositories.django_pago_repository import DjangoPagoRepository
from adapters.infrastructure.services.django_sri_service import DjangoSRIService
from adapters.infrastructure.services.django_email_service import DjangoEmailService
from adapters.api.serializers.factura_serializers import (
    RegistrarCobroSerializer, ReportarPagoSerializer, ValidarPagoSerializer
)

# --- SERIALIZERS LOCALES (Extraídos para limpieza) ---
class CobroLecturaSerializer(serializers.ModelSerializer):
    socio_nombre = serializers.CharField(source='socio.nombres', read_only=True)
    rubro_nombre = serializers.CharField(source='rubro.nombre', read_only=True)
    class Meta:
        model = CuentaPorCobrarModel
        fields = '__all__'

# --- VISTAS ---

class CobroViewSet(viewsets.ViewSet):
    """
    Controlador de Recaudación (Caja y Validaciones).
    """
    permission_classes = [permissions.IsAuthenticated]

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
    @transaction.atomic
    def subir_comprobante(self, request):
        serializer = ReportarPagoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            # Buscamos factura para obtener el SOCIO (Pago se asocia a Socio, no Factura directamente)
            factura = FacturaModel.objects.select_related('socio').get(pk=data['factura_id'])

            if factura.estado == EstadoFactura.PAGADA.value:
                return Response({"error": "Esta factura ya está pagada."}, status=400)

            # 1. Crear Cabecera de Pago (Pendiente de Validación)
            pago = PagoModel.objects.create(
                socio=factura.socio,
                monto_total=data['monto'],
                validado=False,
                observacion=f"Pago web para Factura #{factura.id}"
            )

            # 2. Crear Detalle con la Evidencia (Imagen)
            DetallePagoModel.objects.create(
                pago=pago,
                metodo=MetodoPagoEnum.TRANSFERENCIA.value,
                monto=data['monto'],
                referencia=data['referencia'],
                comprobante_imagen=data['comprobante']
            )

            # 3. Actualizar estado VISUAL de la factura (bloqueo preventivo)
            factura.estado = EstadoFactura.POR_VALIDAR.value
            factura.save()

            return Response({
                "mensaje": "Comprobante recibido. Pendiente de aprobación.",
                "pago_id": pago.id,
                "estado": "PENDIENTE_VALIDACION"
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
        # Listamos Pagos headers
        pagos = PagoModel.objects.filter(validado=False).select_related('socio').prefetch_related('detalles_metodos')

        data = []
        for p in pagos:
            # Obtenemos la evidencia (asumimos 1 por pago web)
            detalle = p.detalles_metodos.first()
            img_url = None
            referencia = "N/A"
            
            if detalle:
                referencia = detalle.referencia
                if detalle.comprobante_imagen:
                    # django-storages genera URL firmada automáticamente si es S3
                    img_url = request.build_absolute_uri(detalle.comprobante_imagen.url)

            data.append({
                "pago_id": p.id,
                "socio": f"{p.socio.nombres} {p.socio.apellidos}",
                "cedula": getattr(p.socio, "cedula", None) or getattr(p.socio, "identificacion", ""),
                "fecha": p.fecha_registro.strftime("%Y-%m-%d %H:%M"),
                "monto": p.monto_total,
                "referencia": referencia,
                "comprobante_url": img_url,
                "observacion": p.observacion
            })
        return Response(data, status=200)

    @action(detail=False, methods=['post'], url_path='validar-transferencia')
    @transaction.atomic
    def validar_transferencia(self, request):
        serializer = ValidarPagoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        pago_id = serializer.validated_data['pago_id']
        accion = serializer.validated_data['accion']
        motivo = serializer.validated_data.get('motivo_rechazo', '')

        try:
            pago = PagoModel.objects.select_for_update().get(id=pago_id)

            if accion == 'RECHAZAR':
                # Si se rechaza, eliminamos el intento para permitir subir otro
                detalle = pago.detalles_metodos.first()
                if detalle and detalle.comprobante_imagen:
                     detalle.comprobante_imagen.delete() # Limpieza S3
                
                # 3. Revertir estado de Factura (Si aplica)
                # Hack: Extraer ID de la observación "Pago web para Factura #123"
                match = re.search(r"Factura #(\d+)", pago.observacion or "")
                if match:
                    factura_id = int(match.group(1))
                    FacturaModel.objects.filter(pk=factura_id).update(estado=EstadoFactura.PENDIENTE.value)

                pago.delete()
                
                return Response({
                    "mensaje": "Pago rechazado y eliminado.",
                    "estado": "RECHAZADO",
                    "pago_id": pago_id,
                    "motivo_rechazo": motivo
                }, status=200)

            elif accion == 'APROBAR':
                # 1. Marcar validado (Evita doble procesamiento)
                if pago.validado:
                     return Response({"mensaje": "Este pago ya fue validado."}, status=400)
                
                pago.validado = True
                pago.save()

                # 2. IMPUTACIÓN DE DEUDA (Lógica FIFO idéntica a ProcesarAbono)
                # Buscamos deuda pendiente del socio
                deudas = CuentaPorCobrarModel.objects.select_for_update().filter(
                    socio=pago.socio,
                    saldo_pendiente__gt=Decimal('0.00')
                ).order_by('fecha_emision')

                monto_disponible = pago.monto_total
                cuentas_pagadas = 0

                for cuenta in deudas:
                    if monto_disponible <= 0:
                        break
                    
                    abono = min(cuenta.saldo_pendiente, monto_disponible)
                    cuenta.saldo_pendiente -= abono
                    if cuenta.saldo_pendiente == 0:
                        cuenta.estado = EstadoCuentaPorCobrar.PAGADA.value
                        # Si tiene factura ligada, actualizar su estado (si aplica)
                        if cuenta.factura:
                            cuenta.factura.estado = EstadoFactura.PAGADA.value
                            cuenta.factura.save()
                    
                    cuenta.save()
                    monto_disponible -= abono
                    cuentas_pagadas += 1

                # 3. Reactivación de Servicio (Check simple)
                servicio = ServicioModel.objects.filter(socio=pago.socio).first()
                msg_extra = ""
                if servicio and servicio.estado == 'SUSPENDIDO':
                    deuda_total = CuentaPorCobrarModel.objects.filter(
                        socio=pago.socio, 
                        saldo_pendiente__gt=0
                    ).aggregate(total=models.Sum('saldo_pendiente'))['total'] or 0
                    
                    if deuda_total <= 0:
                        # Auto-Reconexión (Simplificada)
                        servicio.estado = 'ACTIVO' 
                        servicio.save()
                        msg_extra = " Servicio REACTIVADO."

                return Response({
                    "mensaje": f"Transferencia APROBADA y aplicada a {cuentas_pagadas} deudas.{msg_extra}",
                    "estado": "APROBADO",
                    "pago_id": pago.id,
                    "saldo_restante_pago": monto_disponible
                }, status=200)

        except PagoModel.DoesNotExist:
            return Response({"error": "Pago no encontrado"}, status=404)
        except Exception as e:
            return Response({"error": "Error procesando validación", "detalle": str(e)}, status=500)

class CobroLecturaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista de Lectura de Cuentas por Cobrar.
    Optimizado para Grids de Deudas.
    """
    queryset = CuentaPorCobrarModel.objects.select_related('socio', 'rubro').all().order_by('-fecha_emision')
    serializer_class = CobroLecturaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['socio__identificacion', 'socio__nombres']
