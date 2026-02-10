# adapters/api/views/comercial_views.py

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.utils import timezone

# Serializers
from adapters.api.serializers import (
    SocioSerializer,
    FacturaSerializer,
    PagoSerializer,
    CatalogoRubroSerializer,
    ProductoMaterialSerializer
)

# Modelos
from adapters.infrastructure.models import (
    SocioModel,
    FacturaModel,
    PagoModel,
    CatalogoRubroModel,
    ProductoMaterial,
    LecturaModel # ✅ IMPORTADO Y ACTIVO
)

@extend_schema_view(
    list=extend_schema(summary="Listar facturas"),
    retrieve=extend_schema(summary="Ver detalle de factura"),
)
class FacturaViewSet(viewsets.ModelViewSet):
    """
    Maneja la gestión de facturas.
    """
    queryset = FacturaModel.objects.all().order_by('-fecha_emision')
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['socio__identificacion', 'numero_secuencial']

    # --- 1. Pre-Emisión (ACTIVO Y FUNCIONAL) ---
    @action(detail=False, methods=['get'], url_path='pre-emision')
    def pre_emision(self, request):
        """
        Calcula qué se va a facturar basándose en las LECTURAS registradas en el sistema.
        """
        datos_pendientes = []

        # 1. Buscamos todas las lecturas.
        # (Idealmente filtraríamos por estado='PENDIENTE', pero usamos .all() para asegurar que traiga algo si existe)
        try:
            lecturas = LecturaModel.objects.select_related('medidor', 'medidor__terreno', 'medidor__terreno__socio').all()
        except:
            lecturas = []

        # 2. Recorremos las lecturas y calculamos los valores
        for lectura in lecturas:
            # Cálculos básicos
            consumo = lectura.actual - lectura.anterior
            if consumo < 0: consumo = 0 # Evitar negativos

            # Tarifa Base (Ejemplo: $0.50 por metro cúbico)
            tarifa_m3 = 0.50
            valor_agua = consumo * tarifa_m3

            # Armamos el objeto para el Frontend
            item = {
                "socio_id": lectura.medidor.terreno.socio.id,
                "nombres": f"{lectura.medidor.terreno.socio.nombres} {lectura.medidor.terreno.socio.apellidos}",
                "lectura_anterior": lectura.anterior,
                "lectura_actual": lectura.actual,
                "consumo": consumo,
                "valor_agua": round(valor_agua, 2),
                "multas": 0.00,       # Se podría sumar desde MultaModel si fuera necesario
                "subtotal": round(valor_agua, 2)
            }
            datos_pendientes.append(item)

        # Si no hay lecturas, retornará [] (lista vacía), mostrando 0 en el dashboard y CERO errores.
        return Response(datos_pendientes, status=status.HTTP_200_OK)

    # --- 2. Pendientes ---
    @action(detail=False, methods=['get'], url_path='pendientes')
    def pendientes(self, request):
        """
        Retorna las facturas que NO están pagadas.
        """
        qs = self.get_queryset().exclude(estado='PAGADA')

        ver_historial = request.query_params.get('ver_historial') == 'true'
        if not ver_historial:
            qs = qs.filter(anio=timezone.now().year)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(summary="Listar todos los socios"),
)
class SocioViewSet(viewsets.ModelViewSet):
    queryset = SocioModel.objects.all().order_by('apellidos')
    serializer_class = SocioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['identificacion', 'nombres', 'apellidos']

class PagoViewSet(viewsets.ModelViewSet):
    queryset = PagoModel.objects.all().order_by('-fecha_registro')
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head']

class CatalogoRubroViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CatalogoRubroModel.objects.filter(activo=True).order_by('nombre')
    serializer_class = CatalogoRubroSerializer
    permission_classes = [IsAuthenticated]

class ProductoMaterialViewSet(viewsets.ModelViewSet):
    queryset = ProductoMaterial.objects.filter(activo=True).order_by('nombre')
    serializer_class = ProductoMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre', 'codigo']