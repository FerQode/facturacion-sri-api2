from django.db import models
from core.domain.evento import TipoEvento, EstadoEvento
from core.domain.asistencia import EstadoJustificacion
from adapters.infrastructure.models.socio_model import SocioModel
from adapters.infrastructure.models.factura_model import FacturaModel

class EventoModel(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in TipoEvento])
    fecha = models.DateField()
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in EstadoEvento], default=EstadoEvento.BORRADOR.value)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gobernanza_evento'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

class AsistenciaModel(models.Model):
    evento = models.ForeignKey(EventoModel, on_delete=models.CASCADE, related_name='asistencias')
    socio = models.ForeignKey(SocioModel, on_delete=models.CASCADE, related_name='asistencias')
    asistio = models.BooleanField(default=False)
    estado_justificacion = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in EstadoJustificacion], default=EstadoJustificacion.SIN_SOLICITUD.value)
    
    multa_factura = models.ForeignKey(FacturaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='multas_gobernanza')
    
    observacion = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gobernanza_asistencia'
        unique_together = ('evento', 'socio')
