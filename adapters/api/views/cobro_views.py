# adapters/api/views/cobro_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import serializers

from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase
from core.shared.enums import MetodoPagoEnum

# --- Serializers Locales (DTOs de Entrada) ---
class DetallePagoSerializer(serializers.Serializer):
    metodo = serializers.ChoiceField(choices=[e.value for e in MetodoPagoEnum])
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    referencia = serializers.CharField(required=False, allow_blank=True, help_text="Obligatorio para Transferencia")
    observacion = serializers.CharField(required=False, allow_blank=True)

class RegistrarCobroSerializer(serializers.Serializer):
    factura_id = serializers.IntegerField()
    pagos = DetallePagoSerializer(many=True)

class CobroViewSet(viewsets.ViewSet):
    """
    Maneja la recaudación y registro de pagos.
    """

    @swagger_auto_schema(request_body=RegistrarCobroSerializer)
    @action(detail=False, methods=['post'], url_path='registrar')
    def registrar_cobro(self, request):
        serializer = RegistrarCobroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            uc = RegistrarCobroUseCase()
            # Ejecutamos el caso de uso
            resultado = uc.ejecutar(
                factura_id=serializer.validated_data['factura_id'],
                lista_pagos=serializer.validated_data['pagos']
            )
            return Response(resultado, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)