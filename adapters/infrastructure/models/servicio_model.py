# adapters>infrastucture>models>servicio_model.py
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

    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('SUSPENDIDO', 'Suspendido (Corte)'),
        ('PENDIENTE_RECONEXION', 'Pendiente de Reconexión'),
        ('BAJA', 'De Baja'),
    ]

    socio = models.ForeignKey(SocioModel, on_delete=models.PROTECT, related_name='servicios')
    terreno = models.ForeignKey(TerrenoModel, on_delete=models.PROTECT, related_name='servicios')

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='FIJO')
    # --- GESTIÓN DE ESTADOS Y CORTES ---
    estado = models.CharField(max_length=25, choices=ESTADO_CHOICES, default='ACTIVO')
    orden_trabajo_activa = models.ForeignKey(
        'OrdenTrabajoModel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='servicio_activo_en_orden',
        help_text="Orden de trabajo en curso (ej. Reconexión)"
    )
    meses_mora = models.PositiveIntegerField(default=0, help_text="Meses acumulados de deuda")
    fecha_corte = models.DateField(null=True, blank=True, help_text="Fecha de suspensión del servicio")
    # -----------------------------------

    valor_tarifa = models.DecimalField(max_digits=10, decimal_places=2, default=3.00,
                                       help_text="Costo de la Tarifa Básica (o Fija)")

    # Campos para Tarifa Medida (Configurables)
    tarifa_basica_m3 = models.PositiveIntegerField(default=15, help_text="Metros cúbicos incluidos en la base (Ej: 15)")
    tarifa_excedente_precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.25, 
                                          help_text="Costo por cada m³ adicional (Ej: 0.25)")

    fecha_instalacion = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'servicios_agua'
        verbose_name = 'Servicio de Agua'

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.socio.apellidos}"