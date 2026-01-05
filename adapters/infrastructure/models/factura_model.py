from django.db import models
from django.utils import timezone
from decimal import Decimal
from .socio_model import SocioModel
from .medidor_model import MedidorModel
from .lectura_model import LecturaModel
from core.shared.enums import EstadoFactura

class FacturaModel(models.Model):
    ESTADO_CHOICES = [(estado.value, estado.name) for estado in EstadoFactura]
    
    # Opciones de SRI
    AMBIENTE_CHOICES = ((1, 'PRUEBAS'), (2, 'PRODUCCION'))
    TIPO_EMISION_CHOICES = ((1, 'NORMAL'),)

    socio = models.ForeignKey(SocioModel, on_delete=models.PROTECT, related_name='facturas')
    medidor = models.ForeignKey(MedidorModel, on_delete=models.PROTECT, null=True, blank=True)
    lectura = models.OneToOneField(LecturaModel, on_delete=models.PROTECT, null=True, blank=True)
    
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=EstadoFactura.PENDIENTE.value)
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # --- CAMPOS SRI ---
    sri_ambiente = models.PositiveIntegerField(choices=AMBIENTE_CHOICES, default=1)
    sri_tipo_emision = models.PositiveIntegerField(choices=TIPO_EMISION_CHOICES, default=1)
    
    clave_acceso_sri = models.CharField(max_length=49, null=True, blank=True, unique=True, db_index=True)
    
    # --- ¡CAMPO QUE FALTABA Y CAUSABA EL ERROR! ---
    estado_sri = models.CharField(max_length=50, null=True, blank=True, help_text="Estado devuelto por el SRI (RECIBIDA, AUTORIZADO, etc)")
    # -----------------------------------------------

    fecha_autorizacion_sri = models.DateTimeField(null=True, blank=True)
    xml_autorizado_sri = models.TextField(null=True, blank=True)
    mensaje_error_sri = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'facturas'
        verbose_name = 'Factura'
        ordering = ['-fecha_registro']

class DetalleFacturaModel(models.Model):
    factura = models.ForeignKey(FacturaModel, on_delete=models.CASCADE, related_name='detalles')
    concepto = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=4)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'facturas_detalles'