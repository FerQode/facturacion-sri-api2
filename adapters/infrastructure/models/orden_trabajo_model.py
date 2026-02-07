# adapters>infrastructure>models>orden_trabajo_model.py
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords
from .servicio_model import ServicioModel

class OrdenTrabajoModel(models.Model):
    TIPO_CHOICES = [
        ('CORTE', 'Corte de Servicio'),
        ('RECONEXION', 'Reconexión de Servicio'),
        ('INSPECCION', 'Inspección Técnica'),
        ('INSTALACION', 'Instalación Nueva'),
    ]

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    servicio = models.ForeignKey(ServicioModel, on_delete=models.PROTECT, related_name='ordenes_trabajo')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_ejecucion = models.DateTimeField(null=True, blank=True)
    
    observacion_tecnico = models.TextField(null=True, blank=True, help_text="Informe del operador")
    
    operador_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ordenes_asignadas',
        help_text="Usuario responsable de la ejecución"
    )

    class Meta:
        db_table = 'ordenes_trabajo'
        verbose_name = 'Orden de Trabajo'
        verbose_name_plural = 'Órdenes de Trabajo'

    def __str__(self):
        return f"OT-{self.id} {self.get_tipo_display()} ({self.get_estado_display()})"

    history = HistoricalRecords()
