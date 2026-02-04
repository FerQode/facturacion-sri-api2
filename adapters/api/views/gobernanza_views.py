# adapters/api/views/gobernanza_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from core.use_cases.gobernanza.crear_evento_use_case import CrearEventoUseCase, CrearEventoRequest
from core.use_cases.gobernanza.registrar_asistencia_use_case import RegistrarAsistenciaUseCase
from core.use_cases.gobernanza.cerrar_evento_use_case import CerrarEventoYMultarUseCase
from core.use_cases.gobernanza.procesar_justificacion_use_case import ProcesarJustificacionUseCase

from core.domain.evento import TipoEvento
from adapters.infrastructure.repositories.django_evento_repository import DjangoEventoRepository
from adapters.infrastructure.repositories.django_asistencia_repository import DjangoAsistenciaRepository
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.services.django_email_service import DjangoEmailService

from adapters.infrastructure.models.evento_models import EventoModel, AsistenciaModel
from adapters.api.serializers.gobernanza_serializers import (
    EventoSerializer, CrearEventoRequestSerializer, AsistenciaSerializer,
    RegistrarAsistenciaRequestSerializer, ProcesarJustificacionRequestSerializer
)

class EventoViewSet(viewsets.ModelViewSet):
    queryset = EventoModel.objects.all().order_by('-fecha')
    serializer_class = EventoSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CrearEventoRequestSerializer
        return EventoSerializer

    @swagger_auto_schema(request_body=CrearEventoRequestSerializer)
    def create(self, request, *args, **kwargs):
        serializer = CrearEventoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Inicializar repositorios
        evento_repo = DjangoEventoRepository()
        asistencia_repo = DjangoAsistenciaRepository()
        socio_repo = DjangoSocioRepository()

        # Inicializar Use Case
        use_case = CrearEventoUseCase(evento_repo, asistencia_repo, socio_repo)

        # Ejecutar
        try:
            req = CrearEventoRequest(
                nombre=data['nombre'],
                tipo=TipoEvento(data['tipo']),
                fecha=data['fecha'],
                valor_multa=float(data['valor_multa']),
                seleccion_socios=data['seleccion_socios'],
                barrio_id=data.get('barrio_id'),
                lista_socios_ids=data.get('lista_socios_ids')
            )
            evento = use_case.execute(req)
            
            # Retornar respuesta
            # Serialize the domain object or the model. 
            # Ideally return the model instance if we want to use EventoSerializer (ModelSerializer).
            # But execute returns Domain Object via UseCase.
            # We can re-fetch model or serialize the domain object manually. 
            # Or easier: just return success message or simple data for MVP.
            # But frontend needs ID.
            # Let's map domain back to response dict or serialize it. 
            # EventoSerializer expects Model instance usually. 
            
            return Response({
                "id": evento.id,
                "nombre": evento.nombre,
                "estado": evento.estado.value,
                "mensaje": "Evento creado exitosamente"
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # log e
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def asistencia(self, request, pk=None):
        """
        Retorna la lista de asistencia del evento.
        """
        # Necesitamos el ID del evento. 
        # pk viene de la URL.
        # Validar si existe evento.
        try:
            evento = EventoModel.objects.get(pk=pk)
        except EventoModel.DoesNotExist:
            return Response({"error": "Evento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        asistencias = AsistenciaModel.objects.filter(evento=evento).select_related('socio')
        serializer = AsistenciaSerializer(asistencias, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    @swagger_auto_schema(request_body=RegistrarAsistenciaRequestSerializer)
    def registrar_asistencia(self, request, pk=None):
        """
        Actualiza los presentes. Recibe lista de IDs de socios que asistieron.
        """
        serializer = RegistrarAsistenciaRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Repos y UseCase
        asistencia_repo = DjangoAsistenciaRepository()
        use_case = RegistrarAsistenciaUseCase(asistencia_repo)
        
        try:
            use_case.execute(pk, serializer.validated_data['socios_ids'])
            return Response({"mensaje": "Asistencia actualizada correctamente"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """
        Cierra el evento y genera multas para los ausentes.
        """
        # Repositorios
        evento_repo = DjangoEventoRepository()
        asistencia_repo = DjangoAsistenciaRepository()
        factura_repo = DjangoFacturaRepository()
        email_service = DjangoEmailService()
        socio_repo = DjangoSocioRepository()
        
        use_case = CerrarEventoYMultarUseCase(evento_repo, asistencia_repo, email_service, socio_repo)
        
        try:
            from django.db import transaction
            with transaction.atomic():
                use_case.execute(pk)
            return Response({"mensaje": "Evento cerrado y multas generadas exitosamente"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='justificar')
    @swagger_auto_schema(request_body=ProcesarJustificacionRequestSerializer)
    def justificar(self, request):
        """
        Procesa la justificación de una falta (Aprobar/Rechazar).
        """
        serializer = ProcesarJustificacionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        asistencia_repo = DjangoAsistenciaRepository()
        factura_repo = DjangoFacturaRepository()
        
        use_case = ProcesarJustificacionUseCase(asistencia_repo, factura_repo)
        
        try:
            use_case.execute(data['asistencia_id'], data['decision'], data.get('observacion', ''))
            return Response({"mensaje": f"Justificación {data['decision']} correctamente"})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
