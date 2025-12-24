from django.db import models
from .medidor_model import MedidorModel

class LecturaModel(models.Model):
    """
    Modelo ORM para persistir las lecturas de los medidores.
    """
    id = models.AutoField(primary_key=True)

    # Relación: Si intentas borrar un medidor con lecturas, la BDD lo impedirá (Protección)
    medidor = models.ForeignKey(
        MedidorModel, 
        on_delete=models.PROTECT, 
        related_name='lecturas',
        verbose_name="Medidor Asociado"
    )

    # --- CAMBIO CRÍTICO: Estandarización de nombre y tipo ---
    # Antes: lectura_actual_m3 (int)
    # Ahora: valor (decimal) -> Coincide con core/domain/lectura.py
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor Lectura (m3)"
    )
    
    fecha = models.DateField(verbose_name="Fecha de Toma")
    
    # Campos de Auditoría y Proceso
    observacion = models.TextField(null=True, blank=True)
    esta_facturada = models.BooleanField(default=False, help_text="Indica si esta lectura ya entró en una factura")
    
    # Auditoría técnica (cuándo se insertó el registro en el sistema)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lecturas'
        verbose_name = 'Lectura'
        verbose_name_plural = 'Lecturas'
        get_latest_by = 'fecha'
        ordering = ['-fecha']
        
        # REGLA DE INTEGRIDAD: 
        # Un medidor no debería tener dos lecturas registradas en la misma fecha.
        unique_together = ('medidor', 'fecha')

    def __str__(self):
        return f"Medidor {self.medidor.codigo} - {self.fecha}: {self.valor} m3"