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

    # ✅ NUEVO: Campo para que el socio suba la foto desde el celular
    comprobante_imagen = models.ImageField(
        upload_to='comprobantes/%Y/%m/',
        null=True,
        blank=True,
        help_text="Foto del recibo subida por el socio"
    )

    # ✅ NUEVO: Bandera de validación
    # True = Pago en ventanilla (Cajero lo hizo, es válido automáticamenete).
    # False = Pago reportado por Socio (Requiere revisión).
    validado = models.BooleanField(default=True)

    observacion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago {self.metodo} - ${self.monto} (Fac: {self.factura.id})"