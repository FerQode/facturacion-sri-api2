# adapters/infrastructure/models/socio_model.py
from django.db import models
from django.contrib.auth.models import User # <-- Importamos el usuario de Django
# Importamos el Enum del core para mantener consistencia
from core.shared.enums import RolUsuario

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

    # --- CAMPO NUEVO ---
    # Vinculación con el sistema de autenticación (OneToOne con User de Django)
    # on_delete=models.CASCADE: Si borras el usuario, se borra el socio.
    # null=True, blank=True: Permite que existan socios sin usuario (por si acaso).
    # related_name='perfil_socio': Permite acceder al socio desde el usuario (user.perfil_socio).
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='perfil_socio')

    class Meta:
        db_table = 'socios' # Nombre de la tabla en la BBDD
        verbose_name = 'Socio'

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula})"