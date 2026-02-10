# adapters/api/views/gobernanza_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from adapters.infrastructure.models import EventoModel, SolicitudJustificacionModel
from adapters.api.serializers.gobernanza_serializers import (
    EventoSerializer, 
    RegistroAsistenciaSerializer,
    ResumenMultasSerializer,
    CrearSolicitudSerializer,
    ResolucionSolicitudSerializer
)
from core.use_cases.gobernanza.registrar_asistencia_use_case import RegistrarAsistenciaUseCase
from core.use_cases.gobernanza.procesar_multas_batch_use_case import ProcesarMultasBatchUseCase
from core.use_cases.gobernanza.crear_solicitud_justificacion import CrearSolicitudJustificacionUseCase
from core.use_cases.gobernanza.resolucion_solicitud_justificacion_use_case import ResolucionSolicitudJustificacionUseCase

class EventoViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para Gobernanza.
    Maneja Eventos (CRUD) y acciones de negocio (Asistencia, Multas).
    """
    queryset = EventoModel.objects.all().order_by('-fecha')
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated] # Ajustar según seguridad (IsAdminUser?)

    @action(detail=True, methods=['post'], url_path='registrar-asistencia')
    def registrar_asistencia(self, request, pk=None):
        """
        Endpoint p/ Carga Masiva de Asistencias.
        POST /api/v1/eventos/{id}/registrar-asistencia/
        Body: { "asistencias": [ { "socio_id": 1, "estado": "ASISTIO" } ] }
        """
        # 1. Validar Input Serializer
        # Inyectamos el ID del evento en el contexto o data si fuera necesario, 
        # pero el serializer espera 'evento_id' explícito o lo manejamos aquí.
        data = request.data.copy()
        data['evento_id'] = pk 
        
        serializer = RegistroAsistenciaSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Ejecutar Use Case
        use_case = RegistrarAsistenciaUseCase()
        try:
            resultado = use_case.ejecutar(
                evento_id=pk,
                asistencias=serializer.validated_data['asistencias']
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error interno procesando asistencias.", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='procesar-multas')
    def procesar_multas(self, request, pk=None):
        """
        Endpoint "Martillo": Genera Deuda por Inasistencia.
        POST /api/v1/eventos/{id}/procesar-multas/
        """
        use_case = ProcesarMultasBatchUseCase()
        try:
            resultado = use_case.ejecutar(evento_id=pk)
            output_serializer = ResumenMultasSerializer(resultado)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error generando multas.", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SolicitudJustificacionViewSet(viewsets.ViewSet):
    """
    Gestiona las solicitudes de justificación (Crear, Revisar, Resolver).
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser) # Para subir archivos

    def create(self, request):
        """
        Crear nueva solicitud (Socio o Admin).
        POST /api/v1/justificaciones/
        """
        serializer = CrearSolicitudSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        use_case = CrearSolicitudJustificacionUseCase()
        try:
            resultado = use_case.ejecutar(serializer.validated_data)
            return Response(resultado, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error creando solicitud.", "detalle": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='resolver')
    def resolver(self, request, pk=None):
        """
        Resolver solicitud (Admin).
        POST /api/v1/justificaciones/{id}/resolver/
        """
        serializer = ResolucionSolicitudSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        use_case = ResolucionSolicitudJustificacionUseCase()
        try:
            resultado = use_case.ejecutar(
                solicitud_id=pk, 
                nuevo_estado=serializer.validated_data['estado'],
                observacion_admin=serializer.validated_data.get('observacion_admin', '')
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AsistenciaViewSet(viewsets.ModelViewSet):
    """
    CRUD de Asistencias (Individual). 
    Complementa la carga masiva de Eventos.
    """
    from adapters.infrastructure.models import AsistenciaModel
    queryset = AsistenciaModel.objects.select_related('socio', 'evento').all()
    # Serializer inline para no romper dependencias circulares si no existe archivo
    from rest_framework import serializers
    class AsistenciaInlineSerializer(serializers.ModelSerializer):
        socio_nombre = serializers.CharField(source='socio.nombres', read_only=True)
        evento_nombre = serializers.CharField(source='evento.nombre', read_only=True)
        class Meta:
            model = AsistenciaModel
            fields = '__all__'
    
    serializer_class = AsistenciaInlineSerializer
    permission_classes = [IsAuthenticated]
    from rest_framework import filters
    filter_backends = [filters.SearchFilter]
    search_fields = ['socio__identificacion', 'evento__nombre']
