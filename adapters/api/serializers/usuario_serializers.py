# adapter/api/serializers/usuario_serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User

class UserProfileSerializer(serializers.ModelSerializer):
    # Campos que vienen de la relación con el modelo Socio
    # Usamos 'source' para navegar la relación inversa (User -> Socio)
    # Asumo que en tu modelo Socio tienes: user = models.OneToOneField(User, related_name='socio')
    id_socio = serializers.IntegerField(source='socio.id', read_only=True, default=None)
    identificacion = serializers.CharField(source='socio.identificacion', read_only=True, default='')
    direccion = serializers.CharField(source='socio.direccion', read_only=True, default='')
    telefono = serializers.CharField(source='socio.telefono', read_only=True, default='')
    foto = serializers.ImageField(source='socio.foto', read_only=True, default=None)
    barrio = serializers.CharField(source='socio.barrio.nombre', read_only=True, default='No asignado')

    # Rol (esto ya lo tenías en tu lógica de token, pero es bueno devolverlo aquí también)
    rol = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'id_socio', 'identificacion', 'direccion', 'telefono', 'foto', 'barrio', 'rol'
        ]

    def get_rol(self, obj):
        # Lógica simple para devolver el rol. Ajusta según cómo manejes roles en tu modelo.
        # Si usas grupos de Django:
        if obj.groups.exists():
            return obj.groups.first().name
        # Si el socio tiene un campo tipo_usuario:
        if hasattr(obj, 'socio'):
            return obj.socio.tipo_usuario # O el campo que uses
        return "ADMIN" if obj.is_staff else "SOCIO"
