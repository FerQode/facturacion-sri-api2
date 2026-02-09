# adapters/infrastructure/models/evidencia_orden_model.py
from django.db import models
from .orden_trabajo_model import OrdenTrabajoModel

class EvidenciaOrdenTrabajoModel(models.Model):
    """
    Almacena fotos/archivos que evidencian la ejecución de una Orden de Trabajo.
    Soporta S3 a través de DEFAULT_FILE_STORAGE en settings.
    """
    orden = models.ForeignKey(OrdenTrabajoModel, on_delete=models.CASCADE, related_name='evidencias')
    archivo = models.FileField(upload_to='evidencias_ordenes/%Y/%m/', help_text="Foto o documento de respaldo")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    # Metadatos tecnicos (opcional para geo-referencia)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'evidencias_orden_trabajo'
        verbose_name = 'Evidencia de Orden'
        verbose_name_plural = 'Evidencias de Órdenes'

    def __str__(self):
        return f"Evidencia #{self.id} - OT {self.orden_id}"
