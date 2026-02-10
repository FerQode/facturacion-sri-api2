from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.db.models import Sum, Count, Q
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
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = None 

    @extend_schema(
        summary="Reporte de Cartera Vencida (Aging Report)",
        description="Retorna la lista de socios con deuda pendiente.",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='cartera-vencida')
    def cartera_vencida(self, request):
        # Corrección 2: Lógica Real con FacturaModel/CuentaPorCobrar
        # Buscamos cuentas por cobrar con saldo pendiente
        deudas = CuentaPorCobrarModel.objects.filter(saldo_pendiente__gt=0).select_related('socio', 'rubro')
        
        # Agrupamos por socio (simulado en Python para simplicidad, idealmente annotate)
        reporte = []
        total_general_deuda = 0
        
        # Mapa para agrupar
        socios_map = {}
        
        for deuda in deudas:
            sid = deuda.socio.id
            if sid not in socios_map:
                socios_map[sid] = {
                    "socio_id": sid,
                    "nombres": f"{deuda.socio.nombres} {deuda.socio.apellidos}",
                    "cedula": deuda.socio.identificacion,
                    "total_deuda": 0,
                    "items": 0
                }
            socios_map[sid]["total_deuda"] += float(deuda.saldo_pendiente)
            socios_map[sid]["items"] += 1
            total_general_deuda += float(deuda.saldo_pendiente)

        # Convertir a lista
        lista_socios = list(socios_map.values())
        
        return Response({
            "total_cartera_vencida": total_general_deuda,
            "cantidad_deudores": len(lista_socios),
            "detalle": lista_socios
        }, status=status.HTTP_200_OK)

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
        
        # Filtros de fecha
        filtros = {'validado': True} # Solo pagos validados
        
        if fecha_inicio_str:
            fi = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            filtros['fecha_registro__date__gte'] = fi
        else:
             filtros['fecha_registro__date'] = timezone.now().date() # Default HOY

        if fecha_fin_str:
            ff = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            filtros['fecha_registro__date__lte'] = ff

        # Corrección 1: Usar 'monto_total' en lugar de 'monto'
        pagos = PagoModel.objects.filter(**filtros)
        total_recaudado = pagos.aggregate(total=Sum('monto_total'))['total'] or 0

        # Desglose (opcional, si DetallePagoModel tiene metodo)
        # Asumiendo que queremos solo el total por ahora para cumplir el requerimiento
        
        return Response({
            "fecha_cierre": fecha_inicio_str or str(timezone.now().date()),
            "total_recaudado": total_recaudado,
            "transacciones": pagos.count()
        }, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Dashboard KPIs",
        description="Métricas para el dashboard principal.",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='dashboard-kpis')
    def dashboard(self, request):
        now = timezone.now()
        
        # KPIs Reales
        facturas_mes = FacturaModel.objects.filter(anio=now.year, mes=now.month).count()
        monto_mes = FacturaModel.objects.filter(anio=now.year, mes=now.month).aggregate(t=Sum('total'))['t'] or 0
        pendientes = FacturaModel.objects.filter(estado=EstadoFactura.PENDIENTE.value).count()
        socios_activos = CuentaPorCobrarModel.objects.values('socio').distinct().count()

        return Response({
            "facturacion_mes_actual": float(monto_mes),
            "facturas_emitidas": facturas_mes,
            "facturas_pendientes": pendientes,
            "socios_con_deuda": socios_activos
        }, status=status.HTTP_200_OK)
