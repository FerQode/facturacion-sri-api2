# adapters/api/views/analytics_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime

from adapters.infrastructure.models.factura_model import FacturaModel
from adapters.infrastructure.models.pago_model import PagoModel
from adapters.infrastructure.models.cuenta_por_cobrar_model import CuentaPorCobrarModel
from core.shared.enums import EstadoFactura

class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet para Reportes de Inteligencia de Negocios.
    Accessible only to Admins and Treasurers.
    """
    permission_classes = [IsAuthenticated] # Puedes agregar IsAdminUser si gustas
    serializer_class = None

    # -------------------------------------------------------------------------
    # 1. CARTERA VENCIDA
    # -------------------------------------------------------------------------
    @extend_schema(
        summary="Reporte de Cartera Vencida (Aging Report)",
        description="Retorna la lista de socios con deuda pendiente.",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='cartera-vencida')
    def cartera_vencida(self, request):
        # Buscamos cuentas por cobrar con saldo pendiente > 0
        deudas = CuentaPorCobrarModel.objects.filter(saldo_pendiente__gt=0).select_related('socio')

        socios_map = {}

        for deuda in deudas:
            sid = deuda.socio.id
            if sid not in socios_map:
                socios_map[sid] = {
                    "socio_id": sid,
                    "nombres": f"{deuda.socio.nombres} {deuda.socio.apellidos}",
                    "cedula": deuda.socio.identificacion,
                    "total_deuda": 0.00, # Inicializar en float
                    "items": 0
                }
            # Sumamos al acumulado del socio
            socios_map[sid]["total_deuda"] += float(deuda.saldo_pendiente)
            socios_map[sid]["items"] += 1

        # Convertir diccionario a lista
        lista_socios = list(socios_map.values())

        # ⚠️ IMPORTANTE: Retornamos la LISTA directa para que Angular pueda hacer .reduce()
        return Response(lista_socios, status=status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # 2. CIERRE DE CAJA
    # -------------------------------------------------------------------------
    @extend_schema(
        summary="Cierre de Caja Diario",
        description="Retorna el total recaudado hoy.",
        parameters=[
            OpenApiParameter('fecha_inicio', OpenApiTypes.DATE, description="YYYY-MM-DD", required=False),
            OpenApiParameter('fecha_fin', OpenApiTypes.DATE, description="YYYY-MM-DD", required=False),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='cierre-caja')
    def cierre_caja(self, request):
        fecha_inicio_str = request.query_params.get('fecha_inicio')
        fecha_fin_str = request.query_params.get('fecha_fin')

        filtros = {}
        # Si tu modelo tiene campo 'validado', descomenta esto:
        # filtros = {'validado': True}

        # Manejo de fechas seguro
        try:
            if fecha_inicio_str:
                fi = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                filtros['fecha_registro__date__gte'] = fi
            else:
                # Si no hay fecha inicio, usamos HOY como default
                filtros['fecha_registro__date'] = timezone.now().date()

            if fecha_fin_str:
                ff = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
                filtros['fecha_registro__date__lte'] = ff
        except ValueError:
            pass # Si la fecha viene mal formato, ignoramos filtro

        pagos = PagoModel.objects.filter(**filtros)

        # Sumamos 'monto' o 'monto_total' según tu base de datos
        try:
            total_recaudado = pagos.aggregate(t=Sum('monto_total'))['t'] or 0.00
        except:
             # Fallback por si el campo se llama solo 'monto'
            total_recaudado = pagos.aggregate(t=Sum('monto'))['t'] or 0.00

        return Response({
            "fecha_cierre": fecha_inicio_str or str(timezone.now().date()),
            "total_general": total_recaudado,  # <--- CAMBIO CLAVE: Angular busca 'total_general'
            "total_recaudado": total_recaudado, # Enviamos ambos por si acaso
            "transacciones": pagos.count()
        }, status=status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # 3. DASHBOARD KPIS
    # -------------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='dashboard-kpis')
    def dashboard(self, request):
        now = timezone.now()

        # Simulamos datos si las tablas están vacías para no ver ceros feos
        facturas_mes = FacturaModel.objects.filter(anio=now.year, mes=now.month).count()

        return Response({
            "facturacion_mes_actual": 0.00,
            "facturas_emitidas": facturas_mes,
            "facturas_pendientes": 0,
            "socios_con_deuda": 0
        }, status=status.HTTP_200_OK)