# adapters>infrastructure>models>lectura_model.py
from django.db import models
from simple_history.models import HistoricalRecords
from .medidor_model import MedidorModel

class LecturaModel(models.Model):
    """
    Modelo ORM para persistir las lecturas de los medidores.
    Actualizado para 'Lectura Inmutable': Guarda el estado histórico del cálculo.
    """
    id = models.AutoField(primary_key=True)

    medidor = models.ForeignKey(
        MedidorModel, 
        on_delete=models.PROTECT, 
        related_name='lecturas',
        verbose_name="Medidor Asociado"
    )

    # Lectura Actual (El dato que entra)
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor Lectura (m3)"
    )
    
    # --- NUEVOS CAMPOS DE TRAZABILIDAD (SNAPSHOTS) ---
    
    # Lectura Anterior: Puede ser NULL si es la primera lectura del medidor
    lectura_anterior = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Lectura Anterior (m3)"
    )

    # Consumo Calculado: Se guarda el resultado de la resta. 
    # Fundamental para que la factura no cambie si se edita la lectura anterior en el futuro.
    consumo_del_mes = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0.00,
        verbose_name="Consumo Calculado (m3)"
    )

    # --- PERIODOS FISCALES (Integridad Contable) ---
    anio = models.PositiveSmallIntegerField(default=2025, verbose_name="Año Fiscal")
    mes = models.PositiveSmallIntegerField(default=1, verbose_name="Mes Fiscal")
    # -----------------------------------------------

    fecha = models.DateField(verbose_name="Fecha de Toma")
    
    observacion = models.TextField(null=True, blank=True)
    esta_facturada = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lecturas'
        verbose_name = 'Lectura'
        verbose_name_plural = 'Lecturas'
        get_latest_by = 'fecha'
        ordering = ['-fecha']
        # Evita 2 lecturas para el mismo medidor en el mismo mes fiscal
        unique_together = ['medidor', 'anio', 'mes']

    def __str__(self):
        return f"Medidor {self.medidor_id} - {self.fecha}: {self.valor} m3"
        
    history = HistoricalRecords()