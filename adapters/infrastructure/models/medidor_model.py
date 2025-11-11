from django.db import models
from .socio_model import SocioModel

class MedidorModel(models.Model):
    socio = models.ForeignKey(SocioModel, on_delete=models.CASCADE, related_name='medidores')
    codigo = models.CharField(max_length=50, unique=True)
    esta_activo = models.BooleanField(default=True)
    observacion = models.TextField(null=True, blank=True)
    tiene_medidor_fisico = models.BooleanField(default=True)

    class Meta:
        db_table = 'medidores'
        verbose_name = 'Medidor'

    def __str__(self):
        return self.codigo