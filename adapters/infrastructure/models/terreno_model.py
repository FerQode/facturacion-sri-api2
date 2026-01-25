# adapters>infrastructure>models>terreno_model.py
from django.db import models
from .socio_model import SocioModel
from .barrio_model import BarrioModel

class TerrenoModel(models.Model):
    """
    Representa el punto de suministro o propiedad física.
    Relaciona un Socio (Dueño) con un Barrio (Ubicación Geográfica).
    """
    id = models.AutoField(primary_key=True)
    
    # Relación: Un socio tiene N terrenos
    socio = models.ForeignKey(
        SocioModel, 
        on_delete=models.CASCADE, 
        related_name='terrenos'
    )
    
    # Relación: Ubicación física del terreno
    barrio = models.ForeignKey(
        BarrioModel, 
        on_delete=models.PROTECT, 
        related_name='terrenos_ubicados'
    )
    
    direccion = models.CharField(
        max_length=200,
        verbose_name="Dirección/Referencia",
        help_text="Ej: Lote vacío frente a la escuela"
    )
    
    # Flag para saber si se le debe cobrar básico aunque no tenga medidor
    es_cometida_activa = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.barrio.nombre} - {self.direccion} ({self.socio.nombres})"

    class Meta:
        db_table = 'terrenos'
        verbose_name = 'Terreno'
        verbose_name_plural = 'Terrenos'