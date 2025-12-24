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

class TerrenoViewSet(viewsets.ViewSet):
    """
    Controlador para la gestión completa de Terrenos (CRUD + Procesos de Negocio).
    Incluye correcciones para la UI de listado y acciones de mantenimiento.
    """

    def _get_repositories(self):
        """Helper para instanciar todos los repositorios necesarios"""
        return {
            "terreno": DjangoTerrenoRepository(),
            "medidor": DjangoMedidorRepository(),
            "socio": DjangoSocioRepository(),
            "barrio": DjangoBarrioRepository(),
            "lectura": DjangoLecturaRepository()
        }

    # =================================================================
    # 1. CREAR (POST)
    # =================================================================
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
            
            # Nota: serializer.to_dto() debe estar implementado en tu serializer, 
            # o puedes usar RegistrarTerrenoDTO(**serializer.validated_data)
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
    # 2. LISTAR (GET) - CORREGIDO PARA FRONTEND ✅
    # =================================================================
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('socio_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Filtrar por Socio"),
            openapi.Parameter('barrio_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description="Filtrar por Barrio"),
        ]
    )
    def list(self, request):
        repos = self._get_repositories()
        repo_terreno = repos['terreno']
        repo_medidor = repos['medidor'] # Necesario para el join manual

        socio_id = request.query_params.get('socio_id')
        barrio_id = request.query_params.get('barrio_id')
        
        terrenos = []

        # Lógica de filtrado
        if socio_id:
            terrenos = repo_terreno.list_by_socio_id(int(socio_id))
        elif barrio_id:
            terrenos = repo_terreno.list_by_barrio_id(int(barrio_id))
        else:
            return Response({"mensaje": "Filtre por ?socio_id=X o ?barrio_id=Y"}, status=status.HTTP_200_OK)

        # Construcción de respuesta enriquecida (Mashup de datos)
        data = []
        for t in terrenos:
            # Buscamos si este terreno tiene medidor activo
            medidor = repo_medidor.get_by_terreno_id(t.id)

            data.append({
                "id": t.id,
                "direccion": t.direccion,
                "nombre_barrio": t.nombre_barrio if hasattr(t, 'nombre_barrio') else "N/A",
                "es_cometida_activa": t.es_cometida_activa,
                "socio_id": t.socio_id,
                
                # Campos calculados para la UI
                "tiene_medidor": True if medidor else False,
                "codigo_medidor": medidor.codigo if medidor else None,
                "marca_medidor": medidor.marca if medidor else None,
                "estado_medidor": medidor.estado if medidor else "SIN MEDIDOR"
            })

        return Response(data, status=status.HTTP_200_OK)

    # =================================================================
    # 3. DETALLE (GET ID)
    # =================================================================
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
    # 4. ACTUALIZAR (PATCH)
    # =================================================================
    @swagger_auto_schema(request_body=TerrenoActualizacionSerializer)
    def partial_update(self, request, pk=None):
        serializer = TerrenoActualizacionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        repo = DjangoTerrenoRepository()
        terreno = repo.get_by_id(int(pk))
        if not terreno:
             return Response({"error": "Terreno no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        data = serializer.validated_data
        
        if 'direccion' in data:
            terreno.direccion = data['direccion']
        if 'barrio_id' in data:
            terreno.barrio_id = data['barrio_id']
        if 'es_cometida_activa' in data:
            terreno.es_cometida_activa = data['es_cometida_activa']

        repo.save(terreno)

        return Response({"mensaje": "Datos actualizados correctamente"}, status=status.HTTP_200_OK)

    # =================================================================
    # 5. REEMPLAZAR MEDIDOR (ACTION POST)
    # =================================================================
    @swagger_auto_schema(
        method='post',
        operation_description="Reemplaza un medidor dañado por uno nuevo.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['lectura_final_viejo', 'motivo_cambio', 'codigo_nuevo', 'marca_nueva'],
            properties={
                'lectura_final_viejo': openapi.Schema(type=openapi.TYPE_NUMBER),
                'motivo_cambio': openapi.Schema(type=openapi.TYPE_STRING),
                'codigo_nuevo': openapi.Schema(type=openapi.TYPE_STRING),
                'marca_nueva': openapi.Schema(type=openapi.TYPE_STRING),
                'lectura_inicial_nuevo': openapi.Schema(type=openapi.TYPE_NUMBER, default=0.0),
            }
        ),
        responses={200: "Cambio exitoso", 400: "Error de validación"}
    )
    @action(detail=True, methods=['post'], url_path='reemplazar-medidor')
    def reemplazar_medidor(self, request, pk=None):
        data = request.data
        repos = self._get_repositories()
        
        # Auditoría simple
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
        except (ValueError, TypeError):
            return Response({"error": "Datos inválidos: Lecturas deben ser numéricas"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Datos incompletos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uc = ReemplazarMedidorUseCase(
                medidor_repo=repos['medidor'],
                lectura_repo=repos['lectura']
            )
            nuevo_medidor = uc.ejecutar(dto)
            
            return Response({
                "mensaje": "Cambio de medidor registrado exitosamente",
                "nuevo_codigo": nuevo_medidor.codigo,
                "estado": nuevo_medidor.estado
            }, status=status.HTTP_200_OK)

        except (EntityNotFoundException, BusinessRuleException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)