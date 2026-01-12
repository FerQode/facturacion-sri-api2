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
        # Lógica de negocio básica: Si no hay vencimiento, damos 30 días
        if 'fecha_vencimiento' not in data:
            data['fecha_vencimiento'] = data['fecha_emision'] + timedelta(days=30)
        
        if data['fecha_vencimiento'] < data['fecha_emision']:
            raise serializers.ValidationError(
                "La fecha de vencimiento no puede ser anterior a la fecha de emisión."
            )
        return data

class EnviarFacturaSRISerializer(serializers.Serializer):
    """
    Valida la solicitud para re-enviar una factura al SRI.
    """
    factura_id = serializers.IntegerField(required=True)

class ConsultarAutorizacionSerializer(serializers.Serializer):
    """
    Valida la consulta de estado mediante clave de acceso (49 dígitos).
    """
    clave_acceso = serializers.CharField(
        required=True,
        min_length=49,
        max_length=49
    )

class EmisionMasivaSerializer(serializers.Serializer):
    """
    Valida los parámetros para facturación masiva.
    """
    mes = serializers.IntegerField(min_value=1, max_value=12)
    anio = serializers.IntegerField(min_value=2020)
    usuario_id = serializers.IntegerField(required=False)

# --- SERIALIZERS PARA COBROS ---

class DetallePagoSerializer(serializers.Serializer):
    """
    Estructura de un abono individual (ej: $5.00 en Efectivo).
    """
    metodo = serializers.ChoiceField(choices=[(tag.name, tag.value) for tag in MetodoPagoEnum])
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    referencia = serializers.CharField(
        required=False, 
        allow_blank=True, 
        help_text="Número de comprobante (Obligatorio para Transferencia)"
    )
    observacion = serializers.CharField(required=False, allow_blank=True)

class RegistrarCobroSerializer(serializers.Serializer):
    """
    Valida la recepción de pagos mixtos para una factura.
    """
    factura_id = serializers.IntegerField()
    pagos = DetallePagoSerializer(many=True, allow_empty=False)


# =============================================================================
# 2. SERIALIZERS DE SALIDA (RESPUESTA AL FRONTEND)
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
    
    # Totales
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    impuestos = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Datos SRI
    sri_estado = serializers.CharField(source='estado_sri', allow_null=True, required=False)
    sri_mensaje = serializers.CharField(source='sri_mensaje_error', allow_null=True, required=False)
    sri_clave_acceso = serializers.CharField(allow_null=True, required=False)

    # Detalles anidados
    detalles = DetalleFacturaSerializer(many=True)

# --- SERIALIZER DE PRE-VISUALIZACIÓN (CORREGIDO) ---

class LecturaPendienteSerializer(serializers.Serializer):
    """
    Serializer para mostrar la pre-visualización de facturas (pendientes).
    Ayuda al Frontend a saber qué campos mostrar en la tabla de 'Pendientes de Generar'.
    """
    # Identificadores
    id = serializers.IntegerField(help_text="ID de la Lectura")
    medidor_codigo = serializers.CharField(allow_null=True)
    socio_nombre = serializers.CharField()
    cedula = serializers.CharField()
    
    # ✅ CORREGIDO: Quitamos source='fecha' porque el dict de entrada ya trae 'fecha_lectura'
    fecha_lectura = serializers.DateField() 

    # Datos de Consumo
    lectura_anterior = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # ✅ CORREGIDO: Quitamos source='valor' (Seguramente el dict ya trae 'lectura_actual')
    lectura_actual = serializers.DecimalField(max_digits=10, decimal_places=2) 
    
    # ✅ CORREGIDO: Quitamos source='consumo_del_mes_m3' (El dict trae 'consumo')
    consumo = serializers.DecimalField(max_digits=10, decimal_places=2)

    # Montos Calculados (Simulación)
    monto_agua = serializers.DecimalField(max_digits=10, decimal_places=2)
    multas_mingas = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_pagar = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    detalle_multas = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        allow_empty=True
    )