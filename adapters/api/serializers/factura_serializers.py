# adapters/api/serializers/factura_serializers.py

from rest_framework import serializers
from datetime import date, timedelta

class GenerarFacturaSerializer(serializers.Serializer):
    """
    Valida el JSON de entrada para el Caso de Uso GenerarFacturaDesdeLecturaUseCase.
    Actúa como el "portero" (gatekeeper) de la API, asegurando que los
    datos sean correctos antes de pasarlos al "cerebro" (core).
    """
    # 1. Campos Requeridos
    # El ID de la lectura que vamos a facturar
    lectura_id = serializers.IntegerField(required=True)
    # La fecha en que se emite la factura
    fecha_emision = serializers.DateField(required=True)
    
    # 2. Campo Opcional (Buena Práctica)
    # Permitimos que el frontend envíe una fecha de vencimiento,
    # pero si no lo hace, la calcularemos nosotros.
    fecha_vencimiento = serializers.DateField(required=False)

    def validate(self, data):
        """
        Método de validación de DRF para reglas de negocio complejas
        que involucran múltiples campos.
        """
        # 3. Lógica de Negocio en el "Portero"
        # Si no nos envían fecha de vencimiento, le asignamos 30 días por defecto.
        if 'fecha_vencimiento' not in data:
            data['fecha_vencimiento'] = data['fecha_emision'] + timedelta(days=30)
        
        # 4. Regla de Validación
        # Nos aseguramos de que la factura no venza antes de ser emitida.
        if data['fecha_vencimiento'] < data['fecha_emision']:
            # Esta excepción se convierte automáticamente en un error HTTP 400
            raise serializers.ValidationError(
                "La fecha de vencimiento no puede ser anterior a la fecha de emisión."
            )
            
        # 5. Devolvemos los datos limpios y validados
        # Estos datos (data) son los que se pasarán al DTO del Caso de Uso.
        return data
    
    # --- AÑADIR ESTA NUEVA CLASE AL FINAL ---

class EnviarFacturaSRISerializer(serializers.Serializer):
    """
    Valida el JSON de entrada para el Caso de Uso EnviarFacturaSRIUseCase.
    Solo necesita el ID de la factura que ya existe.
    """
    factura_id = serializers.IntegerField(required=True)