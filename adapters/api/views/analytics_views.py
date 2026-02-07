# adapters/api/views/analytics_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from core.use_cases.reporting.generar_reporte_cartera_uc import GenerarReporteCarteraUseCase
from core.use_cases.reporting.generar_cierre_caja_uc import GenerarCierreCajaUseCase
from adapters.infrastructure.models.factura_model import FacturaModel
from core.shared.enums import EstadoFactura

class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet para Reportes de Inteligencia de Negocios.
    Solo accesible para Administradores y Tesoreros (IsAdminUser).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    # ⚠️ IMPORTANTE: 'serializer_class = None' evita que drf-spectacular intente adivinar
    # y falle. Al poner None, le obligamos a mirar los @extend_schema.
    serializer_class = None 

    @extend_schema(
        summary="Reporte de Cartera Vencida (Aging Report)",
        description="Retorna la lista de socios con deuda, clasificada por antigüedad (Corriente, 1-3 meses, >3 meses).",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='cartera-vencida')
    def cartera_vencida(self, request):
        use_case = GenerarReporteCarteraUseCase()
        data = use_case.execute()
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cierre de Caja Diario",
        description="Retorna el total recaudado hoy (o en rango de fechas), desglosado por Efectivo/Transferencia.",
        parameters=[
            OpenApiParameter('fecha_inicio', OpenApiTypes.DATE, description="YYYY-MM-DD", required=False),
            OpenApiParameter('fecha_fin', OpenApiTypes.DATE, description="YYYY-MM-DD", required=False),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='cierre-caja')
    def cierre_caja(self, request):
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        # Simple conversión de strings a dates si existen
        from datetime import datetime
        d_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date() if fecha_inicio else None
        d_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date() if fecha_fin else None

        use_case = GenerarCierreCajaUseCase()
        data = use_case.execute(fecha_inicio=d_inicio, fecha_fin=d_fin)
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Dashboard KPIs (Ejecutivo)",
        description="Métricas rápidas para la pantalla de inicio del Tesorero.",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'], url_path='dashboard-kpis')
    def dashboard(self, request):
        # Lógica ligera directamente aquí o en otro UC pequeño
        from django.utils import timezone
        now = timezone.now()
        
        total_facturado_mes = FacturaModel.objects.filter(anio=now.year, mes=now.month).count() 
        facturas_pendientes = FacturaModel.objects.filter(estado=EstadoFactura.PENDIENTE.value).count()
        
        kpis = {
            "facturas_emitidas_mes": total_facturado_mes,
            "pendientes_cobro": facturas_pendientes,
            "status": "online"
        }
        return Response(kpis, status=status.HTTP_200_OK)
