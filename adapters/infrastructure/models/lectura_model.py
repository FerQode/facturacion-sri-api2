from django.db import models
from .medidor_model import MedidorModel

class LecturaModel(models.Model):
    medidor = models.ForeignKey(MedidorModel, on_delete=models.PROTECT, related_name='lecturas')
    fecha_lectura = models.DateField()
    lectura_actual_m3 = models.PositiveIntegerField()
    lectura_anterior_m3 = models.PositiveIntegerField()
    
    @property
    def consumo_del_mes_m3(self) -> int:
        return self.lectura_actual_m3 - self.lectura_anterior_m3

    class Meta:
        db_table = 'lecturas'
        verbose_name = 'Lectura'
        get_latest_by = 'fecha_lectura' # Útil para el repositorio