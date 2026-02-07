# adapters>infrastructure>models>catalogo_models.py
from django.db import models
from simple_history.models import HistoricalRecords
from core.shared.enums import TipoRubro

class CatalogoRubroModel(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=[(t.value, t.name) for t in TipoRubro], default=TipoRubro.AGUA_POTABLE.value)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    iva = models.BooleanField(default=False, help_text="Aplica IVA")
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'catalogo_rubros'
        verbose_name = 'Rubro'
        verbose_name_plural = 'Catálogo de Rubros'

    def __str__(self):
        return f"{self.nombre} (${self.valor_unitario})"

    history = HistoricalRecords()
