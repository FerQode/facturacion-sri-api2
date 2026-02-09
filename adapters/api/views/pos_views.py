# adapters/api/views/pos_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from adapters.api.serializers.pos_serializers import VentaDirectaSerializer
from core.use_cases.pos.facturar_venta_directa import FacturarVentaDirectaUseCase

class POSViewSet(viewsets.ViewSet):
    """
    Punto de Venta (Point of Sale).
    Venta directa de materiales e inventario.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='vender')
    def vender(self, request):
        """
        Registra una venta directa, descuenta stock y factura.
        POST /api/v1/pos/vender/
        """
        serializer = VentaDirectaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        use_case = FacturarVentaDirectaUseCase()
        try:
            resultado = use_case.ejecutar(
                cliente_id=serializer.validated_data['cliente_id'],
                items=serializer.validated_data['items'],
                forma_pago=serializer.validated_data['forma_pago']
            )
            return Response(resultado, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Error procesando venta.", "detalle": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
