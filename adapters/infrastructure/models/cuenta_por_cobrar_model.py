# adapters>infrastructure>models>cuenta_por_cobrar_model.py
from django.db import models
from simple_history.models import HistoricalRecords
from .socio_model import SocioModel
from .factura_model import FacturaModel
from core.shared.enums import EstadoCuentaPorCobrar
from .catalogo_models import CatalogoRubroModel

class CuentaPorCobrarModel(models.Model):
    # Relaciones base
    socio = models.ForeignKey(SocioModel, on_delete=models.PROTECT, related_name='cuentas_por_cobrar')
    factura = models.ForeignKey(FacturaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='cuentas_por_cobrar')
    
    # Detalle de la Deuda
    rubro = models.ForeignKey(CatalogoRubroModel, on_delete=models.PROTECT)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Fechas y Estado
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    
    estado = models.CharField(
        max_length=50, 
        choices=[(e.value, e.name) for e in EstadoCuentaPorCobrar],
        default=EstadoCuentaPorCobrar.PENDIENTE.value
    )
    
    # Trazabilidad
    origen_referencia = models.CharField(max_length=100, null=True, blank=True, help_text="ID Lectura, Multa, etc.")

    class Meta:
        db_table = 'cuentas_por_cobrar'
        verbose_name = 'Cuenta por Cobrar'
        verbose_name_plural = 'Cuentas por Cobrar'
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return f"{self.rubro.nombre} - ${self.saldo_pendiente} ({self.socio})"

    history = HistoricalRecords()
