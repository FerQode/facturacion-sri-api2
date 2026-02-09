# adapters/api/views/billing_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.shortcuts import get_object_or_404
from decimal import Decimal

from adapters.api.serializers.billing_serializers import (
    AbonoInputSerializer, 
    AbonoOutputSerializer,
    EstadoCuentaSerializer
)
from core.use_cases.billing.process_payment import ProcesarAbonoUseCase
from adapters.infrastructure.models import SocioModel, ServicioModel, CuentaPorCobrarModel

class ProcesarAbonoView(APIView):
    """
    Vista transaccional para procesar abonos (WRITE MODEL).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Procesar Abono de Deuda",
        description="""
        Registra un pago parcial o total.
        - Imputación FIFO (lo más antiguo se paga primero).
        - Genera recibo interno.
        - Si se paga todo y estaba suspendido -> Genera Orden de Reconexión.
        """,
        request=AbonoInputSerializer,
        responses={
            200: OpenApiResponse(response=AbonoOutputSerializer, description="Pago exitoso"),
            400: OpenApiResponse(description="Error de validación (ej: Saldo insuficiente)"),
            500: OpenApiResponse(description="Error interno")
        },
        tags=['Billing']
    )
    def post(self, request):
        serializer = AbonoInputSerializer(data=request.data)
        if serializer.is_valid():
            datos = serializer.validated_data
            try:
                use_case = ProcesarAbonoUseCase()
                resultado = use_case.ejecutar(
                    socio_id=datos['socio_id'],
                    monto_abono=datos['monto'],
                    usuario_id=request.user.id
                )
                return Response(AbonoOutputSerializer(resultado).data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"🔥 Error en ProcesarAbono: {e}")
                return Response({"error": "Error interno al procesar el pago."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Corrección de Sintaxis: Return al mismo nivel del if
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultarEstadoCuentaView(APIView):
    """
    Vista de consulta para el cajero (READ MODEL).
    Muestra la deuda actual y el estado del servicio antes de cobrar.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Consultar Estado de Cuenta del Socio",
        description="Retorna la deuda total pendiente, estado del servicio y lista de facturas por pagar.",
        responses={200: EstadoCuentaSerializer},
        tags=['Billing']
    )
    def get(self, request, socio_id):
        # 1. Buscar Socio
        socio = get_object_or_404(SocioModel, id=socio_id)
        
        # 2. Buscar Servicio (Si tiene agua potable)
        servicio = ServicioModel.objects.filter(socio=socio, activo=True).first()
        estado_servicio = servicio.estado if servicio else "SIN_SERVICIO"
        servicio_id = servicio.id if servicio else None
        
        # 3. Buscar Deuda Pendiente
        cuentas_pendientes = CuentaPorCobrarModel.objects.filter(
            socio=socio,
            saldo_pendiente__gt=Decimal('0.00')
        ).order_by('fecha_emision')
        
        deuda_total = sum(c.saldo_pendiente for c in cuentas_pendientes)
        
        # 4. Construir Respuesta DTO
        items = []
        for c in cuentas_pendientes:
            concepto = f"Deuda #{c.id}"
            if c.factura:
                concepto = f"Factura SRI {c.factura.numero_secuencial if c.factura.numero_secuencial else 'S/N'}"
            elif c.multa:
                concepto = f"Multa: {c.multa.motivo}"
            
            items.append({
                'id': c.id,
                'fecha_emision': c.fecha_emision,
                'concepto': concepto,
                'saldo_pendiente': c.saldo_pendiente,
                # Corrección de Esquema: Usar monto_inicial en lugar de monto_total
                'total_original': c.monto_inicial
            })
            
        data = {
            'socio_id': socio.id,
            'nombre_socio': f"{socio.apellidos} {socio.nombres}".strip(),
            'identificacion': socio.identificacion,
            'servicio_id': servicio_id,
            'estado_servicio': estado_servicio,
            'deuda_total': deuda_total,
            'items_pendientes': items
        }
        
        serializer = EstadoCuentaSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
