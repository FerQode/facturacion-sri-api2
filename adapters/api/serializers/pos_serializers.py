# adapters/api/serializers/pos_serializers.py
from rest_framework import serializers
from core.shared.enums import MetodoPagoEnum

class ItemVentaSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)

class VentaDirectaSerializer(serializers.Serializer):
    cliente_id = serializers.IntegerField()
    items = serializers.ListField(child=ItemVentaSerializer(), allow_empty=False)
    forma_pago = serializers.ChoiceField(choices=[(m.value, m.name) for m in MetodoPagoEnum])
