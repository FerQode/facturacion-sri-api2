from rest_framework import viewsets, filters, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

# Importacion Segura de Modelos
from adapters.infrastructure.models import (
    AsistenciaModel,
    MultaModel,
    OrdenTrabajoModel,
    MedidorModel,
    CuentaPorCobrarModel
)

# --- Serializers Inline (Para evitar tocar archivos de serializers existentes) ---
class AsistenciaSerializer(serializers.ModelSerializer):
    socio_nombre = serializers.CharField(source='socio.nombres', read_only=True)
    evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)
    class Meta:
        model = AsistenciaModel
        fields = '__all__'

class MultaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MultaModel
        fields = '__all__'

class OrdenTrabajoSerializer(serializers.ModelSerializer):
    servicio_str = serializers.StringRelatedField(source='servicio', read_only=True)
    class Meta:
        model = OrdenTrabajoModel
        fields = '__all__'

class MedidorSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedidorModel
        fields = '__all__'

class CobroLecturaSerializer(serializers.ModelSerializer):
    """Solo lectura para visualizar deudas"""
    socio_nombre = serializers.CharField(source='socio.nombres', read_only=True)
    rubro_nombre = serializers.CharField(source='rubro.nombre', read_only=True)
    class Meta:
        model = CuentaPorCobrarModel
        fields = '__all__'


# --- ViewSets Faltantes ---

class AsistenciaViewSet(viewsets.ModelViewSet):
    """
    CRUD de Asistencias (Individual). Aparte del masivo en EventoViewSet.
    """
    queryset = AsistenciaModel.objects.select_related('socio', 'evento').all()
    serializer_class = AsistenciaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['socio__identificacion', 'evento__nombre']

class MultaViewSet(viewsets.ModelViewSet):
    """
    Gestión de Multas (Gobernanza).
    """
    queryset = MultaModel.objects.all().order_by('-fecha_registro')
    serializer_class = MultaSerializer
    permission_classes = [IsAuthenticated]

class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    """
    Gestión de Órdenes de Trabajo (Operativa).
    """
    queryset = OrdenTrabajoModel.objects.all().order_by('-fecha_generacion')
    serializer_class = OrdenTrabajoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['servicio__socio__identificacion', 'id']

class CortesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista especializada de Órdenes de Trabajo tipo CORTE.
    """
    queryset = OrdenTrabajoModel.objects.filter(tipo='CORTE').order_by('-fecha_generacion')
    serializer_class = OrdenTrabajoSerializer
    permission_classes = [IsAuthenticated]

class MedidorViewSet(viewsets.ModelViewSet):
    """
    Gestión de Medidores Físicos.
    """
    queryset = MedidorModel.objects.all()
    serializer_class = MedidorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['serial', 'marca']

class CobroLecturaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista de Lectura de Cuentas por Cobrar.
    Complementa al CobroViewSet transaccional.
    """
    queryset = CuentaPorCobrarModel.objects.select_related('socio', 'rubro').all().order_by('-fecha_emision')
    serializer_class = CobroLecturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['socio__identificacion', 'socio__nombres']
