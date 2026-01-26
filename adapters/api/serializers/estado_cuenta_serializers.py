from rest_framework import serializers

class DeudaSerializer(serializers.Serializer):
    factura_id = serializers.IntegerField()
    periodo = serializers.CharField()
    detalle = serializers.CharField()
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)
    consumo_m3 = serializers.IntegerField(required=False, allow_null=True)
    archivo_xml = serializers.CharField(required=False, allow_null=True)
    archivo_pdf = serializers.CharField(required=False, allow_null=True)

class PropiedadSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    direccion = serializers.CharField()
    tipo_servicio = serializers.CharField()
    medidor = serializers.CharField(required=False, allow_null=True)
    deudas = DeudaSerializer(many=True)

class ObligacionGeneralSerializer(serializers.Serializer):
    factura_id = serializers.IntegerField()
    tipo = serializers.CharField()
    concepto = serializers.CharField()
    fecha_evento = serializers.DateField(required=False, allow_null=True)
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)

class PagoHistorialSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    recibo_nro = serializers.CharField()
    archivo_pdf = serializers.CharField(required=False, allow_null=True)

class ResumenFinancieroSerializer(serializers.Serializer):
    total_deuda = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad_facturas_pendientes = serializers.IntegerField()

class SocioResumenSerializer(serializers.Serializer):
    nombres = serializers.CharField()
    identificacion = serializers.CharField()
    email = serializers.CharField()

class EstadoCuentaSerializer(serializers.Serializer):
    socio = SocioResumenSerializer()
    resumen_financiero = ResumenFinancieroSerializer()
    propiedades = PropiedadSerializer(many=True)
    obligaciones_generales = ObligacionGeneralSerializer(many=True)
    historial_pagos_recientes = PagoHistorialSerializer(many=True)
