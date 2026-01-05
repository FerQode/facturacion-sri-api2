from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# El DTO del Core
from core.use_cases.dtos import RegistrarLecturaDTO
# El Caso de Uso (El "Cerebro")
from core.use_cases.registrar_lectura_uc import RegistrarLecturaUseCase
# Las Implementaciones (El "Cuerpo")
from adapters.infrastructure.repositories.django_lectura_repository import DjangoLecturaRepository
from adapters.infrastructure.repositories.django_medidor_repository import DjangoMedidorRepository

# El Serializer (El "Portero")
# CORRECCIÓN: Importamos también el LecturaResponseSerializer
from adapters.api.serializers.lectura_serializers import (
    RegistrarLecturaSerializer, 
    LecturaResponseSerializer
)

# Las Excepciones del Core
from core.shared.exceptions import MedidorNoEncontradoError

class RegistrarLecturaAPIView(APIView):
    """
    Endpoint de API para registrar una nueva lectura.
    Refactorizado para soportar 'Lectura Inmutable'.
    """
    def post(self, request, *args, **kwargs):
        # 1. Validar la entrada (Serializer de Input)
        input_serializer = RegistrarLecturaSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Convertir a DTO del Core
        dto = RegistrarLecturaDTO(**input_serializer.validated_data)

        # 3. Inyección de Dependencias
        lectura_repo = DjangoLecturaRepository()
        medidor_repo = DjangoMedidorRepository()
        
        # 4. Instanciar el Caso de Uso
        use_case = RegistrarLecturaUseCase(
            lectura_repo=lectura_repo, 
            medidor_repo=medidor_repo
        )

        # 5. Ejecutar la lógica de negocio
        try:
            # Aquí obtenemos la Entidad con 'consumo_del_mes_m3' ya calculado y persistido
            lectura_creada = use_case.execute(dto)

            # --- CORRECCIÓN CRÍTICA ---
            # Antes: Construcción manual que fallaba al buscar .consumo_calculado
            # Ahora: Usamos el Serializer de Respuesta para formatear la salida.
            # Esto mapea automáticamente la Entidad al JSON correcto.
            response_serializer = LecturaResponseSerializer(lectura_creada)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        # 6. Manejar errores de negocio
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            # Captura errores como "Lectura actual menor a anterior"
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)