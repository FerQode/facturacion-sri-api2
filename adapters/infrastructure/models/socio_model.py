from django.db import models
# Importamos el Enum del core para mantener consistencia
from core.domain.shared.enums import RolUsuario

class SocioModel(models.Model):
    # Usamos 'choices' para mapear el Enum a la BBDD
    ROL_CHOICES = [(rol.value, rol.name) for rol in RolUsuario]

    cedula = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    barrio = models.CharField(max_length=100)
    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default=RolUsuario.SOCIO.value)
    esta_activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'socios' # Nombre de la tabla en PostgreSQL
        verbose_name = 'Socio'

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula})"