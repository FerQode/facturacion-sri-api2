# adapters/infrastructure/models/inventario_models.py
from django.db import models
from simple_history.models import HistoricalRecords
from .catalogo_models import CatalogoRubroModel

class ProductoMaterial(models.Model):
    """
    Representa materiales o productos físicos que se venden en ventanilla (POS).
    Ej: Tubos, Llaves de paso, Accesorios.
    """
    rubro = models.ForeignKey(CatalogoRubroModel, on_delete=models.PROTECT, related_name='materiales', help_text="Rubro contable asociado")
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=50, unique=True, help_text="SKU o Código Auxiliar para SRI")
    
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=4, help_text="Precio base sin impuestos")
    stock_actual = models.IntegerField(default=0)
    
    # Configuración SRI
    graba_iva = models.BooleanField(default=True, verbose_name="Graba IVA")
    codigo_impuesto_sri = models.CharField(max_length=4, default="2", help_text="2=IVA, 0=0%, 6=No Objeto")
    
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'inventario_materiales'
        verbose_name = 'Material / Producto'
        verbose_name_plural = 'Inventario de Materiales'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre} (${self.precio_unitario})"

    history = HistoricalRecords()
