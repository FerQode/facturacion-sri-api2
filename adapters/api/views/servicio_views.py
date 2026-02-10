# adapters/api/views/servicio_views.py
from rest_framework import viewsets, status, serializers, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

# Modelos
from adapters.infrastructure.models import ServicioModel, OrdenTrabajoModel

# Serializers
from adapters.api.serializers.servicio_serializers import (
    OrdenTrabajoSerializer, CompletarOrdenSerializer, ProcesarCortesBatchSerializer
)
# Use Cases y Tasks
from core.use_cases.servicio.completar_orden_trabajo_use_case import CompletarOrdenTrabajoUseCase
from core.tasks.procesar_cortes_task import procesar_cortes_masivos_task

class CortesViewSet(viewsets.ViewSet):
    """
    Gestión de Cortes Masivos.
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='procesar-batch')
    def procesar_batch(self, request):
        """
        Dispara la tarea asíncrona de cortes masivos.
        POST /api/v1/cortes/procesar-batch/
        """
        serializer = ProcesarCortesBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data['confirmar']:
            # Ejecutar Tarea Celery
            task = procesar_cortes_masivos_task.delay()
            return Response({
                "mensaje": "Proceso de cortes iniciado en segundo plano.",
                "task_id": task.id
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response({"error": "Debe confirmar la acción."}, status=status.HTTP_400_BAD_REQUEST)

class OrdenTrabajoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Gestión de Órdenes de Trabajo.
    Permite listar y Completar (subir evidencia).
    """
    queryset = OrdenTrabajoModel.objects.all().order_by('-fecha_generacion')
    serializer_class = OrdenTrabajoSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    # ✅ Habilitamos búsqueda para el Frontend
    filter_backends = [filters.SearchFilter]
    search_fields = ['servicio__socio__identificacion', '=id']

    @action(detail=True, methods=['post'], url_path='completar')
    def completar(self, request, pk=None):
        """
        Completar Orden con Evidencia.
        POST /api/v1/ordenes-trabajo/{id}/completar/
        Form-Data: { archivo_evidencia: <File>, observacion: "..." }
        """
        serializer = CompletarOrdenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        use_case = CompletarOrdenTrabajoUseCase()
        try:
            resultado = use_case.ejecutar(
                orden_id=pk,
                archivo_evidencia=serializer.validated_data['archivo_evidencia'],
                observacion=serializer.validated_data.get('observacion', '')
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error interno.", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
