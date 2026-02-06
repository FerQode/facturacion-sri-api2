# adapters/infrastructure/models/sri_models.py
from django.db import models

class SRISecuencialModel(models.Model):
    """
    Maneja la numeración de documentos del SRI de forma atómica.
    Garantiza que no existan saltos ni duplicados.
    """
    TIPO_COMPROBANTE_CHOICES = [
        ('01', 'FACTURA'),
        ('04', 'NOTA DE CRÉDITO'),
        ('05', 'NOTA DE DÉBITO'),
        ('06', 'GUÍA DE REMISIÓN'),
        ('07', 'RETENCIÓN'),
    ]

    codigo_establecimiento = models.CharField(max_length=3, default='001')
    codigo_punto_emision = models.CharField(max_length=3, default='001')
    tipo_comprobante = models.CharField(max_length=2, choices=TIPO_COMPROBANTE_CHOICES)
    
    # El número actual que se ha usado. 
    # Ejemplo: Si es 600, la siguiente factura será 601.
    secuencia_actual = models.IntegerField(default=0)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sri_secuenciales'
        unique_together = ('codigo_establecimiento', 'codigo_punto_emision', 'tipo_comprobante')
        verbose_name = "Secuencial SRI"
        verbose_name_plural = "Secuenciales SRI"

    def __str__(self):
        return f"{self.get_tipo_comprobante_display()} - {self.secuencia_actual}"
