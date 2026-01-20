# adapters/api/serializers/lectura_serializers.py
from rest_framework import serializers
from adapters.infrastructure.models import LecturaModel

# ✅ AJUSTE 1: Importar desde el archivo de DTOs correcto (según nuestra estructura anterior)
from core.use_cases.lectura_dtos import RegistrarLecturaDTO

# =============================================================================
# 1. SERIALIZERS DE ENTRADA (Input)
# =============================================================================

class RegistrarLecturaSerializer(serializers.Serializer):
    """
    Valida el JSON que envía Angular para registrar una lectura.
    """
    medidor_id = serializers.IntegerField(required=True)

    # ✅ SEMÁNTICA: Usamos 'lectura_actual' para que el Frontend entienda claramente
    lectura_actual = serializers.DecimalField(
        required=True,
        min_value=0,
        max_digits=12,
        decimal_places=2
    )

    fecha_lectura = serializers.DateField(required=True)
    observacion = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def to_dto(self) -> RegistrarLecturaDTO:
        """
        Convierte la data validada en un DTO puro para el Caso de Uso.
        """
        return RegistrarLecturaDTO(
            medidor_id=self.validated_data['medidor_id'],

            # ✅ CORRECCIÓN CRÍTICA:
            # El DTO espera 'lectura_actual', NO 'valor'.
            # Si pasas 'valor', tendrás un TypeError como el anterior.
            lectura_actual=float(self.validated_data['lectura_actual']),

            fecha_lectura=self.validated_data['fecha_lectura'],

            # Asignamos un operador por defecto (Admin) temporalmente.
            # Idealmente, la Vista debería sobrescribir esto con request.user.id
            operador_id=1,

            observacion=self.validated_data.get('observacion')
        )

# =============================================================================
# 2. SERIALIZERS DE SALIDA (Response)
# =============================================================================

class LecturaResponseSerializer(serializers.ModelSerializer):
    """
    Respuesta simple al crear una lectura.
    """
    medidor_id = serializers.IntegerField()

    # ✅ CONSISTENCIA: Usamos el nombre del campo del modelo.
    # Asumo que en tu modelo se llama 'consumo_del_mes' o calculas 'consumo_del_mes_m3'.
    # Si es una propiedad del modelo, no necesitas 'source' si el nombre coincide.
    # Aquí lo estandarizo a 'consumo_del_mes' usando el source correcto.
    consumo_del_mes = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, source='consumo_del_mes_m3'
    )
    lectura_anterior = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = LecturaModel
        fields = [
            'id', 'medidor_id', 'fecha', 'valor',
            'lectura_anterior', 'consumo_del_mes',
            'observacion', 'esta_facturada'
        ]

class LecturaHistorialSerializer(serializers.ModelSerializer):
    """
    Serializer 'Aplanado' (Flattened) optimizado para Tablas de Historial en Angular.
    """
    id = serializers.IntegerField(read_only=True)
    fecha = serializers.DateField(format="%Y-%m-%d")

    # Renombramos 'valor' (BD) a 'lectura_actual' (API) para ser consistentes con el Input
    lectura_actual = serializers.DecimalField(source='valor', max_digits=12, decimal_places=2)

    lectura_anterior = serializers.DecimalField(max_digits=12, decimal_places=2)

    # ✅ CONSISTENCIA: Usamos el mismo source que en el ResponseSerializer
    consumo = serializers.DecimalField(source='consumo_del_mes', max_digits=12, decimal_places=2)

    # Campos calculados / relaciones
    estado = serializers.SerializerMethodField()
    medidor_codigo = serializers.CharField(source='medidor.codigo', default="S/N")
    socio_nombre = serializers.SerializerMethodField()

    class Meta:
        model = LecturaModel
        fields = [
            'id', 'fecha', 'medidor_codigo', 'socio_nombre',
            'lectura_anterior', 'lectura_actual', 'consumo', 'estado'
        ]

    def get_estado(self, obj):
        return "Facturada" if obj.esta_facturada else "Registrada"

    def get_socio_nombre(self, obj):
        try:
            # Navegación segura: Lectura -> Medidor -> Terreno -> Socio
            if obj.medidor and obj.medidor.terreno and obj.medidor.terreno.socio:
                return f"{obj.medidor.terreno.socio.nombres} {obj.medidor.terreno.socio.apellidos}"
            return "Sin Socio"
        except AttributeError:
            return "Datos Incompletos"