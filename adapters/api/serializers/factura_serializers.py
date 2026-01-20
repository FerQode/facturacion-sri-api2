# adapters/api/serializers/factura_serializers.py
from rest_framework import serializers
from datetime import date, timedelta
from core.shared.enums import EstadoFactura, MetodoPagoEnum

# =============================================================================
# 1. SERIALIZERS DE ENTRADA (VALIDACIÓN DE SOLICITUDES)
# =============================================================================

class GenerarFacturaSerializer(serializers.Serializer):
    """
    Valida el JSON para generar una factura individual desde una lectura.
    """
    lectura_id = serializers.IntegerField(required=True)
    fecha_emision = serializers.DateField(required=True)
    fecha_vencimiento = serializers.DateField(required=False)

    def validate(self, data):
        if 'fecha_vencimiento' not in data:
            data['fecha_vencimiento'] = data['fecha_emision'] + timedelta(days=30)

        if data['fecha_vencimiento'] < data['fecha_emision']:
            raise serializers.ValidationError(
                "La fecha de vencimiento no puede ser anterior a la fecha de emisión."
            )
        return data

class EnviarFacturaSRISerializer(serializers.Serializer):
    factura_id = serializers.IntegerField(required=True)

class ConsultarAutorizacionSerializer(serializers.Serializer):
    clave_acceso = serializers.CharField(
        required=True,
        min_length=49,
        max_length=49
    )

class EmisionMasivaSerializer(serializers.Serializer):
    mes = serializers.IntegerField(min_value=1, max_value=12)
    anio = serializers.IntegerField(min_value=2020)
    usuario_id = serializers.IntegerField(required=False)

# =============================================================================
# 2. SERIALIZERS PARA COBROS Y PAGOS (TESORERO / SOCIO)
# =============================================================================

# 1. DTO para cada pago individual (Efectivo, Transferencia, etc.)
class DetallePagoSerializer(serializers.Serializer):
    """
    Estructura de un abono individual (ej: $5.00 en Efectivo).
    """
    metodo = serializers.ChoiceField(choices=[e.value for e in MetodoPagoEnum])
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    referencia = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Número de comprobante (Obligatorio para Transferencia)"
    )
    observacion = serializers.CharField(required=False, allow_blank=True)

# 2. DTO para el Cobro en Ventanilla (Tesorero)
class RegistrarCobroSerializer(serializers.Serializer):
    """
    Valida la recepción de pagos mixtos para una factura.
    """
    factura_id = serializers.IntegerField()
    pagos = DetallePagoSerializer(many=True, allow_empty=False)

# 3. ✅ NUEVO: DTO para que el Socio suba la foto (App Móvil)
class ReportarPagoSerializer(serializers.Serializer):
    factura_id = serializers.IntegerField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    referencia = serializers.CharField(required=True, help_text="Número de comprobante del banco")
    comprobante = serializers.ImageField(required=True, help_text="Foto o captura del pago")

# 4. ✅ NUEVO: DTO para que el Tesorero apruebe/rechace
class ValidarPagoSerializer(serializers.Serializer):
    pago_id = serializers.IntegerField()
    accion = serializers.ChoiceField(choices=['APROBAR', 'RECHAZAR'])
    motivo_rechazo = serializers.CharField(required=False, allow_blank=True)

# =============================================================================
# 3. SERIALIZERS DE SALIDA (RESPUESTA AL FRONTEND)
# =============================================================================

class DetalleFacturaSerializer(serializers.Serializer):
    """Serializa los ítems dentro de la factura"""
    concepto = serializers.CharField()
    cantidad = serializers.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=4)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)

class FacturaResponseSerializer(serializers.Serializer):
    """
    JSON FINAL que recibe el Frontend con los datos de la factura generada.
    """
    id = serializers.IntegerField()
    socio_id = serializers.IntegerField()
    fecha_emision = serializers.DateField()
    fecha_vencimiento = serializers.DateField()
    estado = serializers.ChoiceField(choices=[e.value for e in EstadoFactura])
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    impuestos = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    sri_estado = serializers.CharField(source='estado_sri', allow_null=True, required=False)
    sri_mensaje = serializers.CharField(source='sri_mensaje_error', allow_null=True, required=False)
    sri_clave_acceso = serializers.CharField(allow_null=True, required=False)
    detalles = DetalleFacturaSerializer(many=True)

class LecturaPendienteSerializer(serializers.Serializer):
    """
    Serializer para mostrar la pre-visualización de facturas (pendientes).
    """
    id = serializers.IntegerField(help_text="ID de la Lectura")
    medidor_codigo = serializers.CharField(allow_null=True)
    socio_nombre = serializers.CharField()
    cedula = serializers.CharField()
    fecha_lectura = serializers.DateField()
    lectura_anterior = serializers.DecimalField(max_digits=10, decimal_places=2)
    lectura_actual = serializers.DecimalField(max_digits=10, decimal_places=2)
    consumo = serializers.DecimalField(max_digits=10, decimal_places=2)
    monto_agua = serializers.DecimalField(max_digits=10, decimal_places=2)
    multas_mingas = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_pagar = serializers.DecimalField(max_digits=10, decimal_places=2)
    detalle_multas = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

class DetalleConsumoSocioSerializer(serializers.Serializer):
    """
    Mapea los datos de lectura para el modal 'Detalle de Cobro'.
    """
    lectura_anterior = serializers.DecimalField(max_digits=10, decimal_places=2)
    lectura_actual = serializers.DecimalField(max_digits=10, decimal_places=2, source='valor')
    consumo_total = serializers.DecimalField(max_digits=10, decimal_places=2, source='consumo_del_mes')
    costo_base = serializers.DecimalField(max_digits=10, decimal_places=2)

class SocioPerfilSerializer(serializers.Serializer):
    nombres = serializers.CharField()
    apellidos = serializers.CharField()
    cedula = serializers.CharField()
    direccion = serializers.CharField(allow_blank=True, allow_null=True)

class FacturaSocioHistoricoSerializer(serializers.Serializer):
    """
    Serializer oficial para el historial del socio y RIDE.
    """
    id = serializers.IntegerField()
    fecha_emision = serializers.DateField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    estado = serializers.CharField()
    clave_acceso_sri = serializers.CharField(allow_null=True, required=False)
    socio = SocioPerfilSerializer()
    detalle = DetalleConsumoSocioSerializer(source='lectura', allow_null=True)