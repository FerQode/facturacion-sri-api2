from rest_framework import serializers

class RegistrarLecturaSerializer(serializers.Serializer):
    """
    Valida el JSON para el Caso de Uso RegistrarLecturaUseCase.
    Se mapea 1-a-1 con el RegistrarLecturaDTO del core.
    """
    medidor_id = serializers.IntegerField(required=True)
    lectura_actual_m3 = serializers.IntegerField(required=True, min_value=0)
    fecha_lectura = serializers.DateField(required=True)
    # Asumimos que el ID del operador vendrá en el token,
    # pero por ahora lo pedimos en el JSON para probar.
    operador_id = serializers.IntegerField(required=True)