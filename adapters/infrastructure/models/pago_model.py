# adapters/infrastructure/models/pago_model.py
from django.db import models
from .factura_model import FacturaModel

class PagoModel(models.Model):
    id = models.AutoField(primary_key=True)
    
    factura = models.ForeignKey(
        FacturaModel, 
        on_delete=models.PROTECT, # No se puede borrar la factura si ya tiene pagos
        related_name='pagos_registrados'
    )
    
    metodo = models.CharField(max_length=20) # EFECTIVO, TRANSFERENCIA
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Datos para Transferencia Pichincha
    referencia = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Número de comprobante o referencia bancaria"
    )
    
    observacion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.metodo} - ${self.monto} (Fac: {self.factura.id})"