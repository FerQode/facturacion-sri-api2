# adapters/api/serializers/medidor_serializers.py

from rest_framework import serializers
# ✅ IMPORTANTE: Agregamos LecturaModel a los imports para consultar historial
from adapters.infrastructure.models import MedidorModel, TerrenoModel, LecturaModel

class MedidorSerializer(serializers.ModelSerializer):
    """
    Serializer HÍBRIDO: Funciona con DTOs (del Core) y con Modelos (del ORM).
    Enriquece la respuesta con datos del Barrio, Socio y la Última Lectura registrada.
    """
    nombre_barrio = serializers.SerializerMethodField()
    nombre_socio = serializers.SerializerMethodField()
    direccion_terreno = serializers.SerializerMethodField()
    
    # ✅ Campo calculado: Última lectura (VITAL para validar en frontend)
    lectura_anterior = serializers.SerializerMethodField()

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
            'lectura_anterior', # <--- ¡Asegúrate de que esté aquí!
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

    # ✅ LÓGICA DE TU COMPAÑERO (CORRECTA E INTEGRADA)
    def get_lectura_anterior(self, obj):
        """
        Busca la última lectura registrada para este medidor.
        Si no hay lecturas previas, devuelve la lectura inicial del medidor.
        """
        try:
            # Buscamos en la tabla de lecturas, filtrando por este medidor
            # Ordenamos por fecha descendente (la más nueva primero)
            # Nota: obj.id es el ID del medidor
            ultima_lectura = LecturaModel.objects.filter(medidor_id=obj.id).order_by('-fecha', '-id').first()

            if ultima_lectura:
                return float(ultima_lectura.valor) # Devolvemos la última lectura real
        except Exception:
            pass # Si algo falla, usamos el valor por defecto

        # Si no hay historial, devolvemos la lectura inicial del medidor
        return float(obj.lectura_inicial)


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