# adapters/api/views/billing_views.py
# Fixed indentation
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
                concepto = f"Factura #{c.factura.id}"
            elif c.origen_referencia:
                concepto = f"{c.rubro.nombre}: {c.origen_referencia}"
            else:
                concepto = c.rubro.nombre
            
            items.append({
                'id': c.id,
                'fecha_emision': c.fecha_emision.strftime('%Y-%m-%d'),
                'concepto': concepto,
                'saldo_pendiente': c.saldo_pendiente,
                # Corrección de Esquema: Usar monto_inicial en lugar de monto_total
                'total_original': c.monto_inicial,
                
                # --- UX ENRICHMENT ---
                'nombre_terreno': _get_nombre_terreno(c),
                'tiene_medidor': _check_tiene_medidor(c),
                'detalle_consumo': _get_detalle_consumo(c),
                'mes_facturado': _get_mes_facturado(c),
                'tipo_servicio': _get_tipo_servicio(c),
                'periodo': _get_mes_facturado(c),
                # ✅ ID de Factura para generar PDF en Frontend
                'factura_id': c.factura.id if c.factura else None
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

def _get_nombre_terreno(cuenta):
    if cuenta.factura and cuenta.factura.servicio and cuenta.factura.servicio.terreno:
        t = cuenta.factura.servicio.terreno
        return f"{t.direccion} ({t.barrio.nombre})"
    return "N/A"

def _get_tipo_servicio(cuenta):
    if cuenta.factura and cuenta.factura.servicio:
        return cuenta.factura.servicio.get_tipo_display()
    return "N/A"

def _check_tiene_medidor(cuenta):
    if cuenta.factura and cuenta.factura.servicio:
        return cuenta.factura.servicio.tipo == 'MEDIDO'
    return False

def _get_detalle_consumo(cuenta):
    if not cuenta.factura:
        return "N/A"
        
    fac = cuenta.factura
    if fac.servicio and fac.servicio.tipo == 'MEDIDO' and fac.lectura:
        lect = fac.lectura
        ant = lect.lectura_anterior or 0
        act = lect.valor
        cons = lect.consumo_del_mes
        return f"Lectura: {ant} -> {act} ({cons} m3)"
    elif fac.servicio and fac.servicio.tipo == 'FIJO':
        return "Tarifa Fija (Sin Medidor)"
    return "Consumo General"

def _get_mes_facturado(cuenta):
    if cuenta.factura:
        meses = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 
                 7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
        return f"{meses.get(cuenta.factura.mes, 'Unknown')} {cuenta.factura.anio}"
    return "Varios"
