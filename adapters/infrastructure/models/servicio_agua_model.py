from django.db import models
from .socio_model import SocioModel
from .terreno_model import TerrenoModel

class ServicioAguaModel(models.Model):
    # Tipos de servicio (Enum)
    TIPO_CHOICES = [
        ('FIJO', 'Tarifa Fija (Sin Medidor)'),
        ('MEDIDOR', 'Por Consumo (Con Medidor)'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FIJO')
    valor_tarifa = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Importante: auto_now_add=True pone la fecha de hoy automáticamente al crear
    fecha_instalacion = models.DateTimeField(auto_now_add=True) 
    
    activo = models.BooleanField(default=True)

    # Relaciones (Foreign Keys)
    socio = models.ForeignKey(SocioModel, on_delete=models.CASCADE, related_name='servicios')
    terreno = models.ForeignKey(TerrenoModel, on_delete=models.CASCADE, related_name='servicios_asociados')

    class Meta:
        db_table = 'servicios_agua' # Nombre exacto de tu tabla en MySQL
        verbose_name = 'Servicio de Agua'
        verbose_name_plural = 'Servicios de Agua'

    def __str__(self):
        return f"Servicio {self.tipo} - {self.socio.nombres}"