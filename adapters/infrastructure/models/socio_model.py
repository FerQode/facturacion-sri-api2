# adapters/infrastructure/models/socio_model.py
from django.db import models
from django.contrib.auth.models import User
from core.shared.enums import RolUsuario
from .barrio_model import BarrioModel

class SocioModel(models.Model):
    ROL_CHOICES = [(rol.value, rol.name) for rol in RolUsuario]

    id = models.AutoField(primary_key=True)
    cedula = models.CharField(max_length=10, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    
    # --- CORRECCIÓN DE ESTANDARIZACIÓN ---
    # Renombramos 'barrio_domicilio' a 'barrio' para que coincida con
    # la lógica de 'barrio_id' que usamos en el resto del sistema.
    barrio = models.ForeignKey(
        BarrioModel, 
        on_delete=models.PROTECT, 
        related_name='residentes',
        null=True,     
        blank=True,
        verbose_name="Barrio de Domicilio"
    )
    # -------------------------------------
    
    direccion = models.CharField(max_length=200, null=True, blank=True, help_text="Referencia exacta del domicilio")

    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default=RolUsuario.SOCIO.value)
    esta_activo = models.BooleanField(default=True)

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