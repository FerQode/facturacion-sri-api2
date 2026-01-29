# adapters/infrastructure/models/evento_models.py
from django.db import models
from core.domain.evento import TipoEvento, EstadoEvento
from core.domain.asistencia import EstadoJustificacion, EstadoAsistencia
from adapters.infrastructure.models.socio_model import SocioModel
from adapters.infrastructure.models.factura_model import FacturaModel
from simple_history.models import HistoricalRecords

class EventoModel(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in TipoEvento])
    fecha = models.DateField()
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2)
    # Corrección 1: Estado Programada por defecto
    estado = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in EstadoEvento], default=EstadoEvento.PROGRAMADA.value)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gobernanza_evento'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f"{self.nombre} ({self.fecha})"

class AsistenciaModel(models.Model):
    evento = models.ForeignKey(EventoModel, on_delete=models.CASCADE, related_name='asistencias')
    socio = models.ForeignKey(SocioModel, on_delete=models.CASCADE, related_name='asistencias')
    
    # Corrección 2: Lógica de Estados en lugar de Booleano
    estado = models.CharField(
        max_length=20, 
        choices=[(tag.value, tag.value) for tag in EstadoAsistencia], 
        default=EstadoAsistencia.PENDIENTE.value
    )
    
    estado_justificacion = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in EstadoJustificacion], default=EstadoJustificacion.SIN_SOLICITUD.value)
    
    multa_factura = models.ForeignKey(FacturaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='multas_gobernanza')
    
    observacion = models.TextField(null=True, blank=True, help_text="Motivo de falta o justificacion")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gobernanza_asistencia'
        unique_together = ('evento', 'socio')
        verbose_name = 'Control de Asistencia'
        verbose_name_plural = 'Control de Asistencias'

    def requiere_multa(self):
        """Helper para saber si este registro debe generar deuda"""
        return self.estado == EstadoAsistencia.FALTA.value

    history = HistoricalRecords()
