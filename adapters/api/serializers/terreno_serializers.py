# adapters/api/serializers/terreno_serializers.py

from rest_framework import serializers
from typing import Optional  # Importante para tipado
from core.use_cases.terreno_dtos import RegistrarTerrenoDTO
from adapters.infrastructure.models import TerrenoModel

class TerrenoRegistroSerializer(serializers.Serializer):
    """
    Serializer de Entrada: Valida los datos crudos que vienen del Frontend
    antes de pasarlos al Caso de Uso.
    """
    socio_id = serializers.IntegerField(help_text="ID del socio dueño")
    barrio_id = serializers.IntegerField(help_text="ID del barrio de ubicación")
    direccion = serializers.CharField(max_length=200)
    
    tiene_medidor = serializers.BooleanField(default=False)
    
    # Campos condicionales
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

# Serializer de Salida (MODIFICADO)
class TerrenoLecturaSerializer(serializers.ModelSerializer):
    """
    Serializer de Salida para Terrenos.
    Incluye datos 'aplanados' del medidor para facilitar el consumo del Frontend.
    """
    nombre_barrio = serializers.CharField(source='barrio.nombre', read_only=True)
    nombre_socio = serializers.CharField(source='socio.nombres', read_only=True)
    
    # --- NUEVOS CAMPOS DINÁMICOS ---
    tiene_medidor = serializers.SerializerMethodField()
    codigo_medidor = serializers.SerializerMethodField()
    
    class Meta:
        model = TerrenoModel
        fields = [
            'id', 
            'socio_id', 
            'nombre_socio', 
            'barrio_id', 
            'nombre_barrio', 
            'direccion', 
            'es_cometida_activa',
            # Agregamos los campos extra al JSON final
            'tiene_medidor',
            'codigo_medidor'
        ]

    # --- LÓGICA DE CAMPOS DINÁMICOS ---
    def get_tiene_medidor(self, obj: TerrenoModel) -> bool:
        """Verifica si existe la relación inversa hacia medidor"""
        return hasattr(obj, 'medidor') and obj.medidor is not None

    def get_codigo_medidor(self, obj: TerrenoModel) -> Optional[str]:
        """Obtiene el código si existe el medidor"""
        if hasattr(obj, 'medidor') and obj.medidor is not None:
            return obj.medidor.codigo
        return None

class TerrenoActualizacionSerializer(serializers.Serializer):
    """
    Serializer específico para PATCH/PUT.
    """
    direccion = serializers.CharField(required=False, max_length=200)
    barrio_id = serializers.IntegerField(required=False, help_text="ID del nuevo barrio si se mudó")
    es_cometida_activa = serializers.BooleanField(required=False)

    # Nota: No incluimos medidor aquí porque se maneja en la lógica de la Vista (partial_update).