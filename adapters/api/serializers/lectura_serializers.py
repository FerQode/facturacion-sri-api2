from rest_framework import serializers

class RegistrarLecturaSerializer(serializers.Serializer):
    """
    Valida el JSON para el Caso de Uso RegistrarLecturaUseCase.
    Se mapea 1-a-1 con RegistrarLecturaDTO.
    """
    medidor_id = serializers.IntegerField(required=True)
    lectura_actual_m3 = serializers.IntegerField(required=True, min_value=0)
    fecha_lectura = serializers.DateField(required=True)
    operador_id = serializers.IntegerField(required=True) # Asumiendo que el ID del user logueado