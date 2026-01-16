# adapters/api/views/cobro_views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

# Imports del Dominio
from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase
from core.shared.enums import MetodoPagoEnum
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

# --- Serializers (DTOs) ---
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
    Controlador de Recaudación.
    Orquesta el cobro y la emisión automática al SRI.
    """

    @swagger_auto_schema(
        operation_description="Registra el cobro de una factura y dispara la autorización al SRI.",
        request_body=RegistrarCobroSerializer,
        responses={
            200: "Cobro exitoso y procesado por SRI",
            400: "Regla de Negocio (Ej: Pago incompleto)",
            404: "Factura no encontrada",
            500: "Error técnico interno"
        }
    )
    @action(detail=False, methods=['post'], url_path='registrar')
    def registrar_cobro(self, request):
        serializer = RegistrarCobroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Instanciamos el Caso de Uso
            uc = RegistrarCobroUseCase()
            
            # 2. Ejecutamos la lógica (Cobrar -> Facturar SRI)
            resultado = uc.ejecutar(
                factura_id=serializer.validated_data['factura_id'],
                lista_pagos=serializer.validated_data['pagos']
            )
            
            # 3. Respuesta Exitosa
            return Response(resultado, status=status.HTTP_200_OK)

        except EntityNotFoundException as e:
            # Error 404: La factura no existe en BD
            return Response({"error": "Recurso no encontrado", "detalle": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except BusinessRuleException as e:
            # Error 400: Lógica de negocio (Ya pagada, montos no cuadran)
            return Response({"error": "Error de validación", "detalle": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Error 500: Fallo técnico no controlado (Bug, DB caída, etc)
            return Response({"error": "Error interno del servidor", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)