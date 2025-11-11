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
# LÍNEA CORRECTA
from adapters.api.serializers.lectura_serializers import RegistrarLecturaSerializer
# Las Excepciones del Core
from core.shared.exceptions import MedidorNoEncontradoError

class RegistrarLecturaAPIView(APIView):
    """
    Endpoint de API para registrar una nueva lectura.
    """
    def post(self, request, *args, **kwargs):
        # 1. Validar la entrada (El "Portero")
        serializer = RegistrarLecturaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Convertir a DTO del Core
        dto = RegistrarLecturaDTO(**serializer.validated_data)

        # 3. Inyección de Dependencias: Armar el "Cuerpo"
        #    (Aquí instanciamos las implementaciones de Django)
        lectura_repo = DjangoLecturaRepository()
        medidor_repo = DjangoMedidorRepository()
        
        # 4. Instanciar el "Cerebro" (Caso de Uso)
        use_case = RegistrarLecturaUseCase(
            lectura_repo=lectura_repo, 
            medidor_repo=medidor_repo
        )

        # 5. Ejecutar la lógica de negocio
        try:
            lectura_creada = use_case.execute(dto)
            
            # (Aquí podrías tener un 'LecturaResponseSerializer' para la salida)
            respuesta_data = {
                "id": lectura_creada.id,
                "medidor_id": lectura_creada.medidor_id,
                "consumo_del_mes": lectura_creada.consumo_del_mes_m3
            }
            return Response(respuesta_data, status=status.HTTP_201_CREATED)
        
        # 6. Manejar errores de negocio (definidos en el Core)
        except MedidorNoEncontradoError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Errores inesperados
            return Response({"error": f"Error interno: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)