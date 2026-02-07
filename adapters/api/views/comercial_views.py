# adapters/api/views/comercial_views.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from adapters.api.serializers import (
    SocioSerializer, 
    FacturaSerializer, 
    PagoSerializer,
    CatalogoRubroSerializer,
    ProductoMaterialSerializer
)
from adapters.infrastructure.models import (
    SocioModel, 
    FacturaModel, 
    PagoModel,
    CatalogoRubroModel,
    ProductoMaterial
)

@extend_schema_view(
    list=extend_schema(summary="Listar facturas"),
    retrieve=extend_schema(summary="Ver detalle de factura"),
)
class FacturaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FacturaModel.objects.all().order_by('-fecha_emision')
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['socio__identificacion', 'numero_secuencial']

@extend_schema_view(
    list=extend_schema(summary="Listar todos los socios"),
    retrieve=extend_schema(summary="Obtener un socio por ID"),
    create=extend_schema(summary="Registrar un nuevo socio"),
    update=extend_schema(summary="Actualizar un socio"),
)
class SocioViewSet(viewsets.ModelViewSet):
    queryset = SocioModel.objects.all().order_by('apellidos')
    serializer_class = SocioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['identificacion', 'nombres', 'apellidos']

@extend_schema_view(
    list=extend_schema(summary="Listar historial de pagos"),
    create=extend_schema(summary="Registrar un nuevo pago (Recibo de Cobro) con múltiples métodos"),
    retrieve=extend_schema(summary="Ver detalle de un pago"),
)
class PagoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Pagos (Cabecera + Detalles).
    Soporta creación con detalles anidados (Efectivo, Transferencia, Cheque).
    """
    queryset = PagoModel.objects.all().order_by('-fecha_registro')
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head'] # Pagos no se suelen editar, solo anular

@extend_schema_view(
    list=extend_schema(summary="Catálogo de Rubros"),
    retrieve=extend_schema(summary="Ver detalle de Rubro"),
)
class CatalogoRubroViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CatalogoRubroModel.objects.filter(activo=True).order_by('nombre')
    serializer_class = CatalogoRubroSerializer
    permission_classes = [IsAuthenticated]

@extend_schema_view(
    list=extend_schema(summary="Inventario de Materiales (POS)"),
    create=extend_schema(summary="Registrar nuevo material"),
)
class ProductoMaterialViewSet(viewsets.ModelViewSet):
    queryset = ProductoMaterial.objects.filter(activo=True).order_by('nombre')
    serializer_class = ProductoMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'codigo']
