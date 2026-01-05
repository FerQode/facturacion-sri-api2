# adapters/api/views/terreno_views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# --- Core: Casos de Uso ---
from core.use_cases.registrar_terreno_uc import RegistrarTerrenoUseCase
from core.use_cases.reemplazar_medidor_uc import ReemplazarMedidorUseCase
from core.use_cases.medidor_dtos import ReemplazarMedidorDTO

# --- Core: Excepciones ---
from core.shared.exceptions import (
    EntityNotFoundException, 
    BusinessRuleException, 
    MedidorDuplicadoError
)

# --- Infraestructura: Repositorios ---
from adapters.infrastructure.repositories.django_terreno_repository import DjangoTerrenoRepository
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.repositories.django_barrio_repository import DjangoBarrioRepository
from adapters.infrastructure.repositories.django_lectura_repository import DjangoLecturaRepository

# --- Serializers ---
from adapters.api.serializers.terreno_serializers import (
    TerrenoRegistroSerializer, 
    TerrenoActualizacionSerializer
)
# Necesitamos importar el modelo Medidor para actualizarlo manualmente si es necesario
from adapters.infrastructure.models import MedidorModel

class TerrenoViewSet(viewsets.ViewSet):
    """
    Controlador para la gestión completa de Terrenos (CRUD + Procesos de Negocio).
    """

    def _get_repositories(self):
        return {
            "terreno": DjangoTerrenoRepository(),
            "medidor": DjangoMedidorRepository(),
            "socio": DjangoSocioRepository(),
            "barrio": DjangoBarrioRepository(),
            "lectura": DjangoLecturaRepository()
        }

    # ... (CREATE se mantiene igual) ...
    @swagger_auto_schema(request_body=TerrenoRegistroSerializer)
    def create(self, request):
        serializer = TerrenoRegistroSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            repos = self._get_repositories()
            use_case = RegistrarTerrenoUseCase(
                terreno_repo=repos['terreno'],
                medidor_repo=repos['medidor'],
                socio_repo=repos['socio'],
                barrio_repo=repos['barrio']
            )
            terreno_creado = use_case.ejecutar(serializer.to_dto())
            return Response({
                "mensaje": "Terreno registrado correctamente",
                "id": terreno_creado.id,
                "direccion": terreno_creado.direccion
            }, status=status.HTTP_201_CREATED)
        except (EntityNotFoundException, BusinessRuleException, MedidorDuplicadoError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =================================================================
    # 2. LISTAR (GET) - CORREGIDO ✅
    # =================================================================
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('socio_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('barrio_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ]
    )
    def list(self, request):
        repos = self._get_repositories()
        repo_terreno = repos['terreno']
        repo_medidor = repos['medidor']

        socio_id = request.query_params.get('socio_id')
        barrio_id = request.query_params.get('barrio_id')
        
        terrenos = []
        if socio_id:
            terrenos = repo_terreno.list_by_socio_id(int(socio_id))
        elif barrio_id:
            terrenos = repo_terreno.list_by_barrio_id(int(barrio_id))
        else:
            # Si no hay filtros, listamos todos (útil para debug o listados generales)
            # OJO: Podría ser pesado si hay muchos, pero para tesis está bien.
            # Implementamos un "list_all" básico manual si no existe en el repo
            from adapters.infrastructure.models import TerrenoModel
            qs = TerrenoModel.objects.all()[:100] # Limite seguridad
            terrenos = [repo_terreno._map_model_to_domain(m) for m in qs]

        data = []
        for t in terrenos:
            medidor = repo_medidor.get_by_terreno_id(t.id)
            data.append({
                "id": t.id,
                "direccion": t.direccion,
                "nombre_barrio": t.nombre_barrio if hasattr(t, 'nombre_barrio') else "N/A",
                "es_cometida_activa": t.es_cometida_activa,
                "socio_id": t.socio_id,
                
                # ✅ CORRECCIÓN: Agregar ID de barrio para poder editar
                "barrio_id": t.barrio_id,

                "tiene_medidor": True if medidor else False,
                "codigo_medidor": medidor.codigo if medidor else None,
                "marca_medidor": medidor.marca if medidor else None,
                "estado_medidor": medidor.estado if medidor else "SIN MEDIDOR"
            })

        return Response(data, status=status.HTTP_200_OK)

    # ... (RETRIEVE se mantiene igual) ...
    def retrieve(self, request, pk=None):
        repos = self._get_repositories()
        terreno = repos['terreno'].get_by_id(int(pk))
        if not terreno:
            return Response({"error": "Terreno no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        medidor = repos['medidor'].get_by_terreno_id(terreno.id)

        response = {
            "id": terreno.id,
            "direccion": terreno.direccion,
            "barrio": {
                "id": terreno.barrio_id,
                "nombre": getattr(terreno, 'nombre_barrio', '') 
            },
            "estado_servicio": "ACTIVO" if terreno.es_cometida_activa else "SUSPENDIDO",
            "medidor": None
        }

        if medidor:
            response["medidor"] = {
                "id": medidor.id,
                "codigo": medidor.codigo,
                "marca": medidor.marca,
                "estado": medidor.estado,
                "lectura_inicial": medidor.lectura_inicial
            }
        
        return Response(response, status=status.HTTP_200_OK)

    # =================================================================
    # 4. ACTUALIZAR (PATCH) - MEJORADO ✅
    # =================================================================
    @swagger_auto_schema(request_body=TerrenoActualizacionSerializer)
    def partial_update(self, request, pk=None):
        serializer = TerrenoActualizacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        repos = self._get_repositories()
        repo_terreno = repos['terreno']
        repo_medidor = repos['medidor']

        terreno = repo_terreno.get_by_id(int(pk))
        if not terreno:
             return Response({"error": "Terreno no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        data = serializer.validated_data
        
        # 1. Actualizar Datos del Terreno
        if 'direccion' in data: terreno.direccion = data['direccion']
        if 'barrio_id' in data: terreno.barrio_id = data['barrio_id']
        if 'es_cometida_activa' in data: terreno.es_cometida_activa = data['es_cometida_activa']

        repo_terreno.save(terreno) # Ahora sí usa el save() corregido

        # 2. ✅ NUEVO: Permitir editar código de medidor si viene en el payload (aunque el serializer no lo tenga explícito)
        # Esto es un "plus" para que la UI funcione fluido
        if 'codigo_medidor' in request.data:
            nuevo_codigo = request.data['codigo_medidor']
            medidor_actual = repo_medidor.get_by_terreno_id(terreno.id)
            
            if medidor_actual and nuevo_codigo:
                # Actualización directa vía ORM (bypass temporal para edición rápida)
                try:
                    m_model = MedidorModel.objects.get(id=medidor_actual.id)
                    m_model.codigo = nuevo_codigo
                    m_model.save()
                except Exception as e:
                    print(f"Error actualizando medidor: {e}")

        return Response({"mensaje": "Datos actualizados correctamente"}, status=status.HTTP_200_OK)

    # ... (REEMPLAZAR MEDIDOR se mantiene igual) ...
    @action(detail=True, methods=['post'], url_path='reemplazar-medidor')
    def reemplazar_medidor(self, request, pk=None):
        # (El código es el mismo de arriba, no cambia)
        data = request.data
        repos = self._get_repositories()
        usuario_id = request.user.id if request.user and request.user.is_authenticated else 1
        
        try:
            dto = ReemplazarMedidorDTO(
                terreno_id=int(pk),
                usuario_id=usuario_id,
                lectura_final_viejo=float(data.get('lectura_final_viejo')),
                motivo_cambio=data.get('motivo_cambio'),
                codigo_nuevo=data.get('codigo_nuevo'),
                marca_nueva=data.get('marca_nueva'),
                lectura_inicial_nuevo=float(data.get('lectura_inicial_nuevo', 0.0))
            )
            uc = ReemplazarMedidorUseCase(medidor_repo=repos['medidor'], lectura_repo=repos['lectura'])
            nuevo_medidor = uc.ejecutar(dto)
            return Response({"mensaje": "Cambio registrado", "nuevo_codigo": nuevo_medidor.codigo}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)