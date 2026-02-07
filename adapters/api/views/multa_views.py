# adapters/api/views/multa_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from rest_framework import serializers

# Repositorio
from adapters.infrastructure.repositories.django_multa_repository import DjangoMultaRepository

# Caso de Uso (Lógica de Negocio)
from core.use_cases.gestionar_disputa_multa_uc import GestionarDisputaMultaUseCase
from core.shared.exceptions import EntityNotFoundException, BusinessRuleException

class MultaViewSet(viewsets.ViewSet):
    """
    Gestión de Multas.
    Permite listar y, para administradores, impugnar o rectificar multas.
    """
    
    def get_permissions(self):
        """
        Reglas de seguridad:
        - Impugnar/Rectificar: Solo Administradores.
        - Listar: Cualquier usuario autenticado.
        """
        if self.action in ['impugnar_multa']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def list(self, request):
        """
        GET /api/v1/multas/
        Listar multas. Se puede filtrar por socio ?socio_id=X
        """
        socio_id = request.query_params.get('socio_id')
        repo = DjangoMultaRepository()
        
        try:
            if socio_id:
                # Si implementaste obtener_pendientes_por_socio en el repo
                multas = repo.obtener_pendientes_por_socio(int(socio_id))
                # Nota: obtener_pendientes devuelve diccionarios o entidades, adáptalo según tu repo
                data = multas 
            else:
                # Listar todo (Solo para admin idealmente)
                if not request.user.is_staff:
                    return Response({"error": "Solo admins pueden ver todas las multas"}, status=403)
                # Si tu repo no tiene list_all, devuelve vacío o implementalo
                data = [] 
            
            return Response(data, status=200)
        except Exception as e:
             return Response({"error": str(e)}, status=500)

    @extend_schema(
        summary="Impugnar o Rectificar Multa",
        description="Permite ANULAR (borrado lógico) o RECTIFICAR (cambio de precio) una multa.",
        request=inline_serializer(
            name='ImpugnacionMulta',
            fields={
                'accion': serializers.ChoiceField(choices=['ANULAR', 'RECTIFICAR'], help_text="Valores: 'ANULAR' o 'RECTIFICAR'"),
                'motivo': serializers.CharField(help_text="Razón obligatoria para auditoría"),
                'nuevo_monto': serializers.FloatField(required=False, help_text="Requerido solo si es RECTIFICAR"),
            }
        ),
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['patch'], url_path='impugnar')
    def impugnar_multa(self, request, pk=None):
        """
        Endpoint crítico para corregir errores humanos en multas (Mingas).
        """
        repo = DjangoMultaRepository()
        use_case = GestionarDisputaMultaUseCase(repo)
        
        accion = request.data.get('accion')
        motivo = request.data.get('motivo')
        nuevo_monto = request.data.get('nuevo_monto')
        
        if not motivo:
            return Response({"error": "El motivo es obligatorio para auditoría"}, status=400)

        try:
            if accion == 'ANULAR':
                # Caso A: El socio sí asistió a la minga
                multa = use_case.anular_multa(int(pk), motivo)
            elif accion == 'RECTIFICAR':
                # Caso B: El socio trabajó medio tiempo
                if nuevo_monto is None:
                    return Response({"error": "Falta nuevo_monto para rectificar"}, status=400)
                multa = use_case.rectificar_monto(int(pk), float(nuevo_monto), motivo)
            else:
                return Response({"error": "Acción no válida. Use ANULAR o RECTIFICAR"}, status=400)

            # Respuesta exitosa
            return Response({
                "mensaje": "Multa actualizada correctamente",
                "id": multa.id,
                "nuevo_estado": multa.estado.value if hasattr(multa.estado, 'value') else multa.estado,
                "nuevo_valor": multa.valor,
                "observacion_auditoria": multa.observacion
            }, status=200)

        except (EntityNotFoundException, BusinessRuleException) as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=500)