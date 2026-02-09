# adapters/api/serializers/billing_serializers.py
from rest_framework import serializers
from decimal import Decimal

# ==============================================================================
# 1. WRITE MODEL (Abonos)
# ==============================================================================
class AbonoInputSerializer(serializers.Serializer):
    """
    Serializer para recibir los datos del abono.
    """
    socio_id = serializers.IntegerField(required=True, help_text="ID del socio que realiza el abono.")
    monto = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=Decimal('0.01'), 
        required=True,
        help_text="Monto a abonar (debe ser mayor a 0)."
    )
    metodo_pago = serializers.ChoiceField(
        choices=[
            ('EFECTIVO', 'Efectivo'),
            ('TRANSFERENCIA', 'Transferencia'),
            ('CHEQUE', 'Cheque')
        ],
        required=True,
        help_text="Método de pago utilizado."
    )
    referencia = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True,
        help_text="Referencia del pago (ej: número de transferencia)."
    )

class AbonoOutputSerializer(serializers.Serializer):
    """
    Serializer para la respuesta del abono procesado.
    """
    pago_id = serializers.IntegerField(help_text="ID del pago generado.")
    monto_abonado = serializers.DecimalField(max_digits=10, decimal_places=2)
    saldo_restante_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    cuentas_afectadas = serializers.IntegerField(help_text="Número de cuentas por cobrar imputadas.")
    estado_servicio = serializers.CharField(help_text="Estado actual del servicio tras el pago.")
    mensaje = serializers.CharField(help_text="Mensaje descriptivo del resultado.")

# ==============================================================================
# 2. READ MODEL (Estado de Cuenta)
# ==============================================================================
class DeudaItemSerializer(serializers.Serializer):
    """
    Representa una deuda individual (Factura o Multa) pendiente.
    """
    id = serializers.IntegerField(help_text="ID de la Cuenta por Cobrar")
    fecha_emision = serializers.CharField()
    concepto = serializers.CharField(help_text="Descripción de la deuda (ej: Factura 001-001-123)")
    saldo_pendiente = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_original = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # --- UX FIELDS (Para mostrar en Frontend) ---
    nombre_terreno = serializers.CharField(required=False, allow_null=True)
    tiene_medidor = serializers.BooleanField(default=False)
    detalle_consumo = serializers.CharField(required=False, allow_null=True)
    mes_facturado = serializers.CharField(required=False, allow_null=True)
    tipo_servicio = serializers.CharField(required=False, allow_null=True)
    periodo = serializers.CharField(required=False, allow_null=True)

class EstadoCuentaSerializer(serializers.Serializer):
    """
    Resumen del estado financiero del socio para el cajero.
    """
    socio_id = serializers.IntegerField()
    nombre_socio = serializers.CharField()
    identificacion = serializers.CharField()
    
    # Estado del Servicio
    servicio_id = serializers.IntegerField(allow_null=True)
    estado_servicio = serializers.CharField(help_text="ACTIVO, SUSPENDIDO, etc.")
    
    # Totales
    deuda_total = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Suma de todos los saldos pendientes")
    
    # Detalle
    items_pendientes = DeudaItemSerializer(many=True)
