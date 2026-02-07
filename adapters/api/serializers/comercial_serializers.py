# adapters/api/serializers/comercial_serializers.py
from rest_framework import serializers
from django.db import transaction
from adapters.infrastructure.models import (
    PagoModel, 
    DetallePagoModel, 
    SocioModel, 
    FacturaModel, 
    DetalleFacturaModel,
    CatalogoRubroModel,
    ProductoMaterial
)

# --- 1. Catálogos e Inventario ---
class CatalogoRubroSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogoRubroModel
        fields = '__all__'

class ProductoMaterialSerializer(serializers.ModelSerializer):
    rubro_nombre = serializers.ReadOnlyField(source='rubro.nombre')
    
    class Meta:
        model = ProductoMaterial
        fields = '__all__'

# --- 2. Socios ---
class SocioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocioModel
        fields = '__all__'

# --- 3. Facturación ---
class DetalleFacturaSerializer(serializers.ModelSerializer):
    rubro_nombre = serializers.ReadOnlyField(source='rubro.nombre')
    
    class Meta:
        model = DetalleFacturaModel
        fields = '__all__'

class FacturaSerializer(serializers.ModelSerializer):
    detalles = DetalleFacturaSerializer(many=True, read_only=True)
    socio_nombre = serializers.ReadOnlyField(source='socio.nombres')
    socio_apellido = serializers.ReadOnlyField(source='socio.apellidos')
    
    class Meta:
        model = FacturaModel
        fields = '__all__'

# --- 4. Pagos (Maestro-Detalle) ---
class DetallePagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePagoModel
        fields = ['metodo', 'monto', 'referencia', 'banco_origen']

class PagoSerializer(serializers.ModelSerializer):
    detalles_metodos = DetallePagoSerializer(many=True)
    socio_nombre = serializers.ReadOnlyField(source='socio.nombres')
    socio_apellido = serializers.ReadOnlyField(source='socio.apellidos')
    
    class Meta:
        model = PagoModel
        fields = [
            'id', 
            'socio', 
            'socio_nombre',
            'socio_apellido',
            'numero_comprobante_interno', 
            'monto_total', 
            'observacion', 
            'fecha_registro', 
            'validado', 
            'detalles_metodos'
        ]
        read_only_fields = ['numero_comprobante_interno', 'fecha_registro']

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles_metodos')
        
        with transaction.atomic():
            # 1. Crear Cabecera
            pago = PagoModel.objects.create(**validated_data)
            
            # 2. Crear Detalles
            total_calculado = 0
            for detalle in detalles_data:
                monto = detalle.get('monto', 0)
                total_calculado += monto
                DetallePagoModel.objects.create(pago=pago, **detalle)
            
            # 3. Validación de consistencia (Se podría lanzar excepcion si no cuadra)
            # if pago.monto_total != total_calculado:
            #     raise serializers.ValidationError("El total del pago no coincide con la suma de los métodos.")
                
        return pago
