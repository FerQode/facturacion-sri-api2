# adapters/api/views/medidor_views.py

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema # Documentación automática

# 1. Imports de Infraestructura (Repositorios)
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository
from adapters.infrastructure.repositories.django_terreno_repository import DjangoTerrenoRepository
# --- NUEVOS IMPORTS (Requeridos por Frontend) ---
from adapters.infrastructure.repositories.django_socio_repository import DjangoSocioRepository
from adapters.infrastructure.repositories.django_barrio_repository import DjangoBarrioRepository

# 2. Imports de Serializers (Validación Entrada / Formato Salida)
from adapters.api.serializers.medidor_serializers import (
    MedidorSerializer, 
    RegistrarMedidorSerializer, 
    ActualizarMedidorSerializer
)

# 3. Imports de Casos de Uso (Lógica de Negocio)
from core.use_cases.medidor_uc import (
    ListarMedidoresUseCase, 
    ObtenerMedidorUseCase, 
    CrearMedidorUseCase, 
    ActualizarMedidorUseCase, 
    EliminarMedidorUseCase
)

# 4. Imports de DTOs (Transporte de Datos hacia el Core)
from core.use_cases.medidor_dtos import (
    RegistrarMedidorDTO, 
    ActualizarMedidorDTO
)

# 5. Imports de Excepciones
from core.shared.exceptions import (
    MedidorNoEncontradoError, 
    EntityNotFoundException, 
    BusinessRuleException, 
    MedidorDuplicadoError
)

class MedidorViewSet(viewsets.ViewSet):
    """
    ViewSet para la gestión directa de Medidores.
    Permite el CRUD administrativo y visualización enriquecida para el inventario.
    """
    # permission_classes = [IsAdminUser] # Descomentar para seguridad en producción

    # =================================================================
    # 1. LISTAR (GET) - ACTUALIZADO PARA FRONTEND ✅
    # =================================================================
    @swagger_auto_schema(responses={200: MedidorSerializer(many=True)})
    def list(self, request):
        # 1. Instanciamos repositorio principal
        repo_medidor = DjangoMedidorRepository()
        
        # 2. Instanciamos repositorios auxiliares para cruzar datos
        repo_terreno = DjangoTerrenoRepository()
        repo_socio = DjangoSocioRepository()
        repo_barrio = DjangoBarrioRepository()

        use_case = ListarMedidoresUseCase(repo_medidor)
        
        # 3. Ejecutamos lógica (Obtenemos lista base de medidores)
        medidores = use_case.execute()
        
        # 4. Construimos la respuesta enriquecida (Data Mashup)
        data = []
        for m in medidores:
            # Objeto base con datos del medidor
            info = {
                "id": m.id,
                "codigo": m.codigo,
                "marca": m.marca,
                "estado": m.estado,
                "lectura_inicial": m.lectura_inicial,
                "terreno_id": m.terreno_id,
                "observacion": getattr(m, 'observacion', None),
                
                # Campos calculados para la UI
                "nombre_barrio": "Sin Asignar",
                "nombre_socio": "En bodega / Sin uso"
            }
            
            # Si el medidor está instalado (tiene terreno_id), buscamos detalles
            if m.terreno_id:
                terreno = repo_terreno.get_by_id(m.terreno_id)
                if terreno:
                    # A. Buscar nombre del Barrio
                    if terreno.barrio_id:
                        barrio = repo_barrio.get_by_id(terreno.barrio_id)
                        if barrio:
                            info["nombre_barrio"] = barrio.nombre
                    
                    # B. Buscar nombre del Socio
                    if terreno.socio_id:
                        socio = repo_socio.get_by_id(terreno.socio_id)
                        if socio:
                            info["nombre_socio"] = f"{socio.nombres} {socio.apellidos}"

            data.append(info)

        return Response(data, status=status.HTTP_200_OK)

    # =================================================================
    # 2. DETALLE (GET ID)
    # =================================================================
    @swagger_auto_schema(responses={200: MedidorSerializer()})
    def retrieve(self, request, pk=None):
        repo = DjangoMedidorRepository()
        use_case = ObtenerMedidorUseCase(repo)
        
        try:
            dto = use_case.execute(int(pk))
            # Serializamos la respuesta (Un solo objeto)
            return Response(MedidorSerializer(dto).data, status=status.HTTP_200_OK)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    # =================================================================
    # 3. CREAR (POST) - Con Validación de Serializer
    # =================================================================
    @swagger_auto_schema(
        request_body=RegistrarMedidorSerializer, 
        responses={201: MedidorSerializer()}
    )
    def create(self, request):
        # 1. Validación de Tipos y Campos Obligatorios
        serializer = RegistrarMedidorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Obtener datos limpios
        data = serializer.validated_data
        
        # 3. Construir DTO para el Core
        dto = RegistrarMedidorDTO(
            terreno_id=data['terreno_id'],
            codigo=data['codigo'],
            marca=data.get('marca'),
            lectura_inicial=data.get('lectura_inicial', 0.0),
            observacion=data.get('observacion')
        )

        # 4. Instanciar Dependencias
        medidor_repo = DjangoMedidorRepository()
        terreno_repo = DjangoTerrenoRepository()
        use_case = CrearMedidorUseCase(medidor_repo, terreno_repo)
        
        try:
            # 5. Ejecutar Caso de Uso
            result = use_case.execute(dto)
            return Response(MedidorSerializer(result).data, status=status.HTTP_201_CREATED)
        
        except (EntityNotFoundException, BusinessRuleException, MedidorDuplicadoError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =================================================================
    # 4. ACTUALIZAR (PATCH) - Con Validación de Serializer
    # =================================================================
    @swagger_auto_schema(
        request_body=ActualizarMedidorSerializer,
        responses={200: MedidorSerializer()}
    )
    def partial_update(self, request, pk=None):
        # 1. Validación de Tipos
        serializer = ActualizarMedidorSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        
        # 2. Construir DTO
        dto = ActualizarMedidorDTO(
            codigo=data.get('codigo'),
            marca=data.get('marca'),
            observacion=data.get('observacion')
        )
        
        # 3. Ejecutar Caso de Uso
        medidor_repo = DjangoMedidorRepository()
        use_case = ActualizarMedidorUseCase(medidor_repo)
        
        try:
            result = use_case.execute(int(pk), dto)
            return Response(MedidorSerializer(result).data, status=status.HTTP_200_OK)
        
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except MedidorDuplicadoError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # =================================================================
    # 5. ELIMINAR (DELETE) - Soft Delete
    # =================================================================
    def destroy(self, request, pk=None):
        repo = DjangoMedidorRepository()
        use_case = EliminarMedidorUseCase(repo)
        
        try:
            use_case.execute(int(pk))
            return Response({"mensaje": "Medidor desactivado correctamente"}, status=status.HTTP_204_NO_CONTENT)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)