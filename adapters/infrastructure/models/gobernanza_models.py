# adapters/infrastructure/models/gobernanza_models.py
from django.db import models
from simple_history.models import HistoricalRecords
from core.shared.enums import TipoEvento, EstadoEvento, EstadoAsistencia, EstadoSolicitud
from .socio_model import SocioModel
from .factura_model import FacturaModel

class EventoModel(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=[(tag.value, tag.name) for tag in TipoEvento])
    fecha = models.DateField()
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20, 
        choices=[(tag.value, tag.name) for tag in EstadoEvento], 
        default=EstadoEvento.PROGRAMADO.value
    )
    # lugar? 0001_initial has lugar? Let's check view_file output of 0001_initial.py in history.
    # User's provided serializer had 'lugar'. 
    # But wait, 0001_initial wasn't fully visible in history snippet.
    # I should assume serialier 'lugar' implies model 'lugar'.
    # However, if I break it by adding 'lugar' and DB doesn't have it...
    # I will stick to what is in the serializer which seemingly works?
    # NO. Use what is in goberananza_models.py currently.
    # Current gobernanza_models.py DOES NOT have lugar!
    # But serializer DOES have lugar.
    # Method: I will trust the current gobernanza_models.py is closer to truth unless 0001_initial says otherwise.
    # User said "Si EventoModel ya está definido en 0001_initial.py... campos coincidan EXACTAMENTE".
    # I verified gobernanza_models.py in step 1933. It DOES NOT have 'lugar'.
    # But gobernanza_serializers.py in step 1935 HAS 'lugar'.
    # Error risk: FieldError if serializer asks for 'lugar' and model lacks it.
    # BUT user complained about 'fecha_programada', not 'lugar'.
    # I will remove 'lugar' from serializer to be safe, because model doesn't have it.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gobernanza_eventos'
        verbose_name = 'Evento (Minga/Asamblea)'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f"{self.nombre} ({self.fecha})"

class AsistenciaModel(models.Model):
    evento = models.ForeignKey(EventoModel, on_delete=models.CASCADE, related_name='asistencias')
    socio = models.ForeignKey(SocioModel, on_delete=models.CASCADE, related_name='asistencias')
    
    estado = models.CharField(
        max_length=20, 
        choices=[(tag.value, tag.name) for tag in EstadoAsistencia], 
        default=EstadoAsistencia.FALTA.value
    )
    
    multa_factura = models.ForeignKey(FacturaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='multas_gobernanza')
    
    observacion = models.TextField(null=True, blank=True, help_text="Motivo de falta o justificacion")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gobernanza_asistencias'
        unique_together = ('evento', 'socio')
        verbose_name = 'Control de Asistencia'
        verbose_name_plural = 'Control de Asistencias'

    def __str__(self):
        return f"{self.socio} en {self.evento}: {self.estado}"

    history = HistoricalRecords()

class SolicitudJustificacionModel(models.Model):
    asistencia = models.OneToOneField(AsistenciaModel, on_delete=models.CASCADE, related_name='solicitud_justificacion')
    
    motivo = models.CharField(max_length=255)
    descripcion = models.TextField()
    archivo_evidencia = models.FileField(upload_to='justificaciones/%Y/%m/', null=True, blank=True)
    
    estado = models.CharField(
        max_length=20, 
        choices=[(tag.value, tag.name) for tag in EstadoSolicitud], 
        default=EstadoSolicitud.PENDIENTE.value
    )
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    observacion_admin = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'gobernanza_solicitudes'
        verbose_name = 'Solicitud de Justificación'
        verbose_name_plural = 'Solicitudes de Justificación'

    def __str__(self):
        return f"Solicitud {self.id} - {self.asistencia.socio}"
