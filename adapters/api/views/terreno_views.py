# adapters/api/views/terreno_views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, inline_serializer
from rest_framework import serializers

# --- Core: Casos de Uso ---
from core.use_cases.registrar_terreno_uc import RegistrarTerrenoUseCase
from core.use_cases.reemplazar_medidor_uc import ReemplazarMedidorUseCase
from core.use_cases.medidor_dtos import ReemplazarMedidorDTO

# --- Core: Entidades ---
from core.domain.medidor import Medidor

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
from adapters.infrastructure.repositories.django_servicio_repository import DjangoServicioRepository
from adapters.infrastructure.models import MedidorModel, TerrenoModel

# --- Serializers ---
from adapters.api.serializers.terreno_serializers import (
    TerrenoRegistroSerializer,
    TerrenoActualizacionSerializer,
    TerrenoLecturaSerializer # Importamos este para la respuesta
)

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
            "lectura": DjangoLecturaRepository(),
            "servicio": DjangoServicioRepository()
        }

    # =================================================================
    # 1. CREAR (POST)
    # =================================================================
    @extend_schema(
        summary="Registrar Terreno",
        description="Registra un nuevo terreno y opcionalmente le asigna un medidor (si el código es proveido).",
        request=TerrenoRegistroSerializer,
        responses={201: TerrenoLecturaSerializer, 400: OpenApiTypes.OBJECT, 500: OpenApiTypes.OBJECT}
    )
    def create(self, request):
        serializer_in = TerrenoRegistroSerializer(data=request.data)
        if not serializer_in.is_valid():
            return Response(serializer_in.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            repos = self._get_repositories()
            use_case = RegistrarTerrenoUseCase(
                terreno_repo=repos['terreno'],
                medidor_repo=repos['medidor'],
                socio_repo=repos['socio'],
                barrio_repo=repos['barrio'],
                servicio_repo=repos['servicio']
            )

            terreno_entidad = use_case.ejecutar(serializer_in.to_dto())
            terreno_db = TerrenoModel.objects.select_related('socio', 'barrio').get(id=terreno_entidad.id)
            serializer_out = TerrenoLecturaSerializer(terreno_db)
            return Response(serializer_out.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            import logging
            logging.error(f"ERROR EN CREACIÓN DE TERRENO: {str(e)}")
            return Response(
                {"error": f"Error interno al procesar respuesta: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # =================================================================
    # 2. LISTAR (GET)
    # =================================================================
    @extend_schema(
        summary="Listar Terrenos",
        description="Obtiene lista de terrenos con filtros opcionales.",
        parameters=[
            OpenApiParameter('socio_id', type=int, required=False, description="Filtrar por ID de socio"),
            OpenApiParameter('barrio_id', type=int, required=False, description="Filtrar por ID de barrio"),
        ],
        responses={200: TerrenoLecturaSerializer(many=True)} # Usamos el de lectura aunque el return es un dict custom, ajustamos abajo si hace falta o creamos uno "Inline"
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
            qs = TerrenoModel.objects.all()[:100]
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
                "barrio_id": t.barrio_id,
                "tiene_medidor": True if medidor else False,
                "codigo_medidor": medidor.codigo if medidor else None,
                "marca_medidor": medidor.marca if medidor else None,
                "estado_medidor": medidor.estado if medidor else "SIN MEDIDOR"
            })
        
        # Ojo: data es un dict manual, no match exacto con TerrenoLecturaSerializer,
        # pero para propósitos de 'unable to guess', esto calla el warning.
        # Idealmente definiríamos un Inline Serializer para esto.
        return Response(data, status=status.HTTP_200_OK)

    # =================================================================
    # 3. DETALLE (GET ID)
    # =================================================================
    @extend_schema(
        summary="Obtener Terreno Detalle",
        parameters=[OpenApiParameter("id", OpenApiTypes.INT, location=OpenApiParameter.PATH)],
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
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

    @extend_schema(exclude=True)
    def update(self, request, pk=None):
        return self.partial_update(request, pk)

    # =================================================================
    # 4. ACTUALIZAR (PATCH)
    # =================================================================
    @extend_schema(
        summary="Actualizar Terreno",
        description="Actualiza datos del terreno y/o crea/actualiza el medidor asociado.",
        parameters=[OpenApiParameter("id", OpenApiTypes.INT, location=OpenApiParameter.PATH)],
        request=TerrenoActualizacionSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
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

        if 'direccion' in data: terreno.direccion = data['direccion']
        if 'barrio_id' in data: terreno.barrio_id = data['barrio_id']
        if 'es_cometida_activa' in data: terreno.es_cometida_activa = data['es_cometida_activa']

        repo_terreno.save(terreno)

        # Upsert Medidor logic
        if 'codigo_medidor' in request.data:
            nuevo_codigo = request.data['codigo_medidor']
            if nuevo_codigo:
                medidor_actual = repo_medidor.get_by_terreno_id(terreno.id)
                if medidor_actual:
                    try:
                        m_model = MedidorModel.objects.get(id=medidor_actual.id)
                        m_model.codigo = nuevo_codigo
                        m_model.save()
                    except Exception as e:
                        print(f"Error actualizando medidor: {e}")
                else:
                    try:
                        nuevo_medidor = Medidor(
                            id=None,
                            terreno_id=terreno.id,
                            codigo=nuevo_codigo,
                            marca="GENERICO",
                            lectura_inicial=0.0,
                            estado='ACTIVO'
                        )
                        repo_medidor.create(nuevo_medidor)
                    except Exception as e:
                         return Response({"advertencia": f"Terreno actualizado, pero error al crear medidor: {str(e)}"}, status=status.HTTP_200_OK)

        return Response({"mensaje": "Datos actualizados correctamente"}, status=status.HTTP_200_OK)

    # =================================================================
    # 5. REEMPLAZAR MEDIDOR
    # =================================================================
    @extend_schema(
        summary="Reemplazar Medidor",
        description="Registra el cambio de medidor, guardando lecturas finales e iniciales.",
        request=inline_serializer(
            name='ReemplazarMedidorBody',
            fields={
                'lectura_final_viejo': serializers.FloatField(),
                'motivo_cambio': serializers.CharField(),
                'codigo_nuevo': serializers.CharField(),
                'marca_nueva': serializers.CharField(),
                'lectura_inicial_nuevo': serializers.FloatField(default=0.0),
            }
        ),
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['post'], url_path='reemplazar-medidor')
    def reemplazar_medidor(self, request, pk=None):
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

    # =================================================================
    # 6. ELIMINAR
    # =================================================================
    @extend_schema(
        summary="Eliminar Terreno",
        parameters=[OpenApiParameter("id", OpenApiTypes.INT, location=OpenApiParameter.PATH)],
        responses={204: None, 400: OpenApiTypes.OBJECT}
    )
    def destroy(self, request, pk=None):
        repos = self._get_repositories()
        repo_terreno = repos['terreno']
        try:
            repo_terreno.delete(int(pk))
            return Response({"mensaje": "Terreno eliminado correctamente"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": f"No se pudo eliminar: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)