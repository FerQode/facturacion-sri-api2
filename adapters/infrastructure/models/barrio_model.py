# adapters/infrastructure/models/barrio_model.py
from django.db import models

class BarrioModel(models.Model):
    """
    Modelo de Django que representa la tabla 'barrios' en la base de datos.
    """
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True) # Para Soft Delete

    class Meta:
        db_table = 'barrios'
        verbose_name = 'Barrio'
        verbose_name_plural = 'Barrios'

    def __str__(self):
        return self.nombre