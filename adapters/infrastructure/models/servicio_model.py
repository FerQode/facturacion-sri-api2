#adapters>infrastucture>models>servicio_model.py
from django.db import models
from .socio_model import SocioModel
from .terreno_model import TerrenoModel


class ServicioModel(models.Model):
    """
    Representa el contrato de servicio de agua.
    Puede ser MEDIDO (tiene medidor físico) o FIJO (acometida libre).
    """
    TIPO_CHOICES = [
        ('MEDIDO', 'Medido (Con Medidor)'),
        ('FIJO', 'Tarifa Fija (Sin Medidor)'),
    ]

    socio = models.ForeignKey(SocioModel, on_delete=models.PROTECT, related_name='servicios')
    terreno = models.ForeignKey(TerrenoModel, on_delete=models.PROTECT, related_name='servicios')

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FIJO')
    valor_tarifa = models.DecimalField(max_digits=10, decimal_places=2, default=3.00,
                                       help_text="Valor mensual para tarifa fija")

    fecha_instalacion = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'servicios_agua'
        verbose_name = 'Servicio de Agua'

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.socio.apellidos}"