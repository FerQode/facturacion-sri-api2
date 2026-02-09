# adapters/api/views/inventario_views.py
from rest_framework import viewsets, filters 
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

from adapters.infrastructure.models import ProductoMaterial

class ProductoMaterialSerializer(serializers.ModelSerializer):
    rubro_nombre = serializers.CharField(source='rubro.nombre', read_only=True)
    
    class Meta:
        model = ProductoMaterial
        fields = ['id', 'nombre', 'codigo', 'precio_unitario', 'stock_actual', 'graba_iva', 'rubro_nombre']

class InventarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API de Inventario para búsqueda rápida en POS.
    """
    queryset = ProductoMaterial.objects.filter(activo=True)
    serializer_class = ProductoMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'codigo']
