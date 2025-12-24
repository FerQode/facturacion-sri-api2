# adapters/infrastructure/models/socio_model.py
from django.db import models
from django.contrib.auth.models import User
from core.shared.enums import RolUsuario
# Importamos el modelo Barrio para hacer la relación
from .barrio_model import BarrioModel

class SocioModel(models.Model):
    # Mapeo del Enum a la BBDD
    ROL_CHOICES = [(rol.value, rol.name) for rol in RolUsuario]

    id = models.AutoField(primary_key=True) # Explicito para claridad
    cedula = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    
    # --- CAMBIO IMPORTANTE ---
    # Antes: barrio = models.CharField(...)
    # Ahora: Relación FK. Si borras el barrio, no se borra el socio (PROTECT).
    barrio_domicilio = models.ForeignKey(
        BarrioModel, 
        on_delete=models.PROTECT, 
        related_name='residentes',
        null=True,     # Permitimos null temporalmente para facilitar la migración
        blank=True,
        verbose_name="Barrio de Domicilio"
    )
    
    direccion = models.CharField(max_length=200, null=True, blank=True, help_text="Referencia exacta del domicilio")

    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default=RolUsuario.SOCIO.value)
    esta_activo = models.BooleanField(default=True)

    # Vinculación con Auth de Django
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='perfil_socio'
    )

    class Meta:
        db_table = 'socios'
        verbose_name = 'Socio'
        verbose_name_plural = 'Socios'

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula})"