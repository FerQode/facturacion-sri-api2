# adapters/api/serializers/medidor_serializers.py

from rest_framework import serializers
from adapters.infrastructure.models import MedidorModel, TerrenoModel

class MedidorSerializer(serializers.ModelSerializer):
    """
    Serializer HÍBRIDO: Funciona con DTOs (del Core) y con Modelos (del ORM).
    Enriquece la respuesta con datos del Barrio y Socio usando el ID del terreno.
    """
    nombre_barrio = serializers.SerializerMethodField()
    nombre_socio = serializers.SerializerMethodField()
    direccion_terreno = serializers.SerializerMethodField()

    # Mapeamos terreno_id explícitamente por si viene del DTO como entero simple
    terreno_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = MedidorModel
        fields = [
            'id',
            'terreno_id',
            'codigo',
            'marca',
            'lectura_inicial',
            'estado',
            'observacion',
            'fecha_instalacion',
            # Campos extra para el Frontend
            'nombre_barrio',
            'nombre_socio',
            'direccion_terreno'
        ]

    # --- HELPERS PARA OBTENER EL TERRENO REAL ---
    def _get_terreno_real(self, obj):
        """
        Método auxiliar que intenta conseguir el objeto Terreno de la BD.
        Maneja la dualidad: ¿Es un Modelo Django o es una Entidad/DTO?
        """
        # 1. Si es un Modelo de Django con la relación ya cargada (Caso ideal)
        if hasattr(obj, 'terreno') and obj.terreno:
            return obj.terreno

        # 2. Si es un DTO o Entidad, sacamos el ID y buscamos en BD manualmente
        t_id = getattr(obj, 'terreno_id', None)
        if t_id:
            try:
                # Usamos select_related para traer barrio y socio en 1 sola consulta
                return TerrenoModel.objects.select_related('barrio', 'socio').get(id=t_id)
            except TerrenoModel.DoesNotExist:
                return None
        return None

    # --- MÉTODOS CALCULADOS ---

    def get_nombre_barrio(self, obj):
        terreno = self._get_terreno_real(obj)
        if terreno and terreno.barrio:
            return terreno.barrio.nombre
        return "No Asignado"

    def get_nombre_socio(self, obj):
        terreno = self._get_terreno_real(obj)
        if terreno and terreno.socio:
            return f"{terreno.socio.nombres} {terreno.socio.apellidos}"
        return "Sin Socio (Inventario)"

    def get_direccion_terreno(self, obj):
        terreno = self._get_terreno_real(obj)
        if terreno:
            return terreno.direccion
        return "En Inventario / Bodega"


# --- SERIALIZERS DE ENTRADA (Mantenemos tu lógica limpia aquí) ---

class RegistrarMedidorSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA (Input) para crear un medidor.
    """
    terreno_id = serializers.IntegerField(required=True, help_text="Terreno donde se instalará")
    codigo = serializers.CharField(max_length=50, required=True)
    marca = serializers.CharField(max_length=50, required=False, allow_blank=True)
    lectura_inicial = serializers.FloatField(required=False, default=0.0)
    observacion = serializers.CharField(required=False, allow_blank=True)


class ActualizarMedidorSerializer(serializers.Serializer):
    """
    Serializer de ENTRADA para correcciones (PATCH).
    """
    codigo = serializers.CharField(max_length=50, required=False)
    marca = serializers.CharField(max_length=50, required=False)
    observacion = serializers.CharField(required=False, allow_blank=True)