# adapters>infrastructure>models>pago_model.py
from django.db import models
from simple_history.models import HistoricalRecords
from core.shared.enums import MetodoPagoEnum
from .socio_model import SocioModel
# from .factura_model import FacturaModel # Opcional si el usuario quiere desligar pago de factura directa

class PagoModel(models.Model):
    id = models.AutoField(primary_key=True)
    
    # Cabecera del Pago (Recibo)
    socio = models.ForeignKey(SocioModel, on_delete=models.PROTECT, related_name='pagos_realizados')
    numero_comprobante_interno = models.CharField(max_length=50, unique=True, editable=False, help_text="Código autogenerado")
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    observacion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # Campo opcional para validación de ingresos manuales
    validado = models.BooleanField(default=True)

    class Meta:
        db_table = 'pagos'
        verbose_name = 'Recibo de Pago'
        verbose_name_plural = 'Recibos de Pago'
        ordering = ['-fecha_registro']

    def save(self, *args, **kwargs):
        if not self.numero_comprobante_interno:
            # Generación simple de secuencial (mejorar con secuencia DB en prod)
            import uuid
            self.numero_comprobante_interno = f"REC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_comprobante_interno} - ${self.monto_total} ({self.socio})"

    history = HistoricalRecords()

class DetallePagoModel(models.Model):
    pago = models.ForeignKey(PagoModel, on_delete=models.CASCADE, related_name='detalles_metodos')
    
    metodo = models.CharField(max_length=20, choices=[(m.value, m.name) for m in MetodoPagoEnum])
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Datos específicos
    referencia = models.CharField(max_length=100, null=True, blank=True, help_text="# Transferencia o Cheque")
    banco_origen = models.CharField(max_length=100, null=True, blank=True)
    
    # Evidencia individual si se requiere (opcional)
    comprobante_imagen = models.ImageField(upload_to='comprobantes_pagos/%Y/%m/', null=True, blank=True)

    class Meta:
        db_table = 'pagos_detalles_metodos'
        verbose_name = 'Detalle de Método de Pago'
        verbose_name_plural = 'Detalles de Métodos de Pago'

    def __str__(self):
        return f"{self.metodo}: ${self.monto}"

    history = HistoricalRecords()