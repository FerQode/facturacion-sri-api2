# adapters/api/serializers/terreno_serializers.py

from rest_framework import serializers
from core.use_cases.terreno_dtos import RegistrarTerrenoDTO

class TerrenoRegistroSerializer(serializers.Serializer):
    """
    Serializer de Entrada: Valida los datos crudos que vienen del Frontend
    antes de pasarlos al Caso de Uso.
    """
    socio_id = serializers.IntegerField(help_text="ID del socio dueño")
    barrio_id = serializers.IntegerField(help_text="ID del barrio de ubicación")
    direccion = serializers.CharField(max_length=200)
    
    tiene_medidor = serializers.BooleanField(default=False)
    
    # Campos condicionales (no obligatorios a nivel de estructura, validamos lógica en el UC)
    codigo_medidor = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    marca_medidor = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    lectura_inicial = serializers.FloatField(required=False, default=0.0)
    observacion = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def to_dto(self) -> RegistrarTerrenoDTO:
        """
        Método helper para convertir datos validados en el DTO del Core.
        """
        data = self.validated_data
        return RegistrarTerrenoDTO(
            socio_id=data['socio_id'],
            barrio_id=data['barrio_id'],
            direccion=data['direccion'],
            tiene_medidor=data['tiene_medidor'],
            codigo_medidor=data.get('codigo_medidor'),
            marca_medidor=data.get('marca_medidor'),
            lectura_inicial=data.get('lectura_inicial', 0.0),
            observacion=data.get('observacion')
        )

# Serializer de Salida (Para mostrar el terreno creado)
# Aquí sí podemos usar ModelSerializer para facilitar la lectura
from adapters.infrastructure.models import TerrenoModel

class TerrenoLecturaSerializer(serializers.ModelSerializer):
    nombre_barrio = serializers.CharField(source='barrio.nombre', read_only=True)
    nombre_socio = serializers.CharField(source='socio.nombres', read_only=True)
    
    class Meta:
        model = TerrenoModel
        fields = ['id', 'socio_id', 'nombre_socio', 'barrio_id', 'nombre_barrio', 'direccion', 'es_cometida_activa']

class TerrenoActualizacionSerializer(serializers.Serializer):
    """
    Serializer específico para PATCH/PUT.
    Permite editar dirección y estado. No permite cambiar de dueño (eso sería un traspaso).
    """
    direccion = serializers.CharField(required=False, max_length=200)
    barrio_id = serializers.IntegerField(required=False, help_text="ID del nuevo barrio si se mudó")
    es_cometida_activa = serializers.BooleanField(required=False)

    # Nota: No incluimos medidor aquí. Si se cambia el medidor, 
    # eso suele ser otro proceso (Cambio de Medidor), no una simple edición de texto.