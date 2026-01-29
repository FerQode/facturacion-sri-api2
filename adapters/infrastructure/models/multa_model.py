# adapters/infrastructure/models/multa_model.py
from django.db import models
from simple_history.models import HistoricalRecords
from .socio_model import SocioModel

class MultaModel(models.Model):
    """
    Tabla para registrar sanciones o cargos adicionales (ej: Mingas).
    Se vinculan a un Socio y tienen un estado de pago.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Pago'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada'),
    ]

    id = models.AutoField(primary_key=True)
    socio = models.ForeignKey(
        SocioModel, 
        on_delete=models.CASCADE, 
        related_name='multas'
    )
    
    motivo = models.CharField(max_length=200, help_text="Ej: Falta a Minga Noviembre")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro = models.DateField(auto_now_add=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    
    # Campo opcional: Para saber en qué factura se terminó cobrando esta multa
    factura_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.motivo} - ${self.valor} ({self.estado})"
        
    history = HistoricalRecords()

    class Meta:
        db_table = 'multas'
        verbose_name = 'Multa'
        verbose_name_plural = 'Multas'  