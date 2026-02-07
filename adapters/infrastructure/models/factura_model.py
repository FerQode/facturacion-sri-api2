# adapters.infrastructure.models.factura_model.py
from django.db import models
from django.utils import timezone
from decimal import Decimal
from simple_history.models import HistoricalRecords
from .socio_model import SocioModel
from .medidor_model import MedidorModel
from .lectura_model import LecturaModel
# ### NUEVO: Importamos el modelo de Servicio (Debes haber creado el archivo servicio_model.py primero)
from .servicio_model import ServicioModel
from .catalogo_models import CatalogoRubroModel
from core.shared.enums import EstadoFactura


class FacturaModel(models.Model):
    ESTADO_CHOICES = [(estado.value, estado.name) for estado in EstadoFactura]

    # Opciones de SRI
    AMBIENTE_CHOICES = ((1, 'PRUEBAS'), (2, 'PRODUCCION'))
    TIPO_EMISION_CHOICES = ((1, 'NORMAL'),)

    socio = models.ForeignKey(SocioModel, on_delete=models.PROTECT, related_name='facturas')

    # ### NUEVO: El enlace al Contrato/Servicio
    # Esto permite saber si la factura corresponde a un servicio "FIJO" o "MEDIDO"
    servicio = models.ForeignKey(
        ServicioModel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='facturas',
        help_text="Vincula la factura al contrato de servicio específico (Fijo o Medido)"
    )

    # Estos campos ya los tenías bien configurados como opcionales, los mantenemos así.
    medidor = models.ForeignKey(MedidorModel, on_delete=models.PROTECT, null=True, blank=True)
    lectura = models.OneToOneField(LecturaModel, on_delete=models.PROTECT, null=True, blank=True)

    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # --- PERIODOS FISCALES (Integridad Contable) ---
    anio = models.PositiveSmallIntegerField(default=2025, verbose_name="Año Fiscal")
    mes = models.PositiveSmallIntegerField(default=1, verbose_name="Mes Fiscal")
    # -----------------------------------------------

    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=EstadoFactura.PENDIENTE.value)

    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # --- CAMPOS SRI ---
    sri_ambiente = models.PositiveIntegerField(choices=AMBIENTE_CHOICES, default=1)
    sri_tipo_emision = models.PositiveIntegerField(choices=TIPO_EMISION_CHOICES, default=1)

    clave_acceso_sri = models.CharField(max_length=49, null=True, blank=True, unique=True, db_index=True)
    contribuyente_rimpe = models.BooleanField(default=False, verbose_name="Contribuyente RÉGIMEN RIMPE")
    
    # --- CONTROL DE TIPO DE DOCUMENTO (Fiscal vs Recibo Interno) ---
    es_fiscal = models.BooleanField(default=True, verbose_name="Es Documento Fiscal (SRI)",
                                    help_text="True=Factura Electrónica, False=Recibo Interno/Proforma")
    # --------------------------------------------------------------

    # Mantenemos tu corrección del estado_sri
    estado_sri = models.CharField(max_length=50, null=True, blank=True,
                                  help_text="Estado devuelto por el SRI (RECIBIDA, AUTORIZADO, etc)")

    fecha_autorizacion_sri = models.DateTimeField(null=True, blank=True)
    xml_autorizado_sri = models.TextField(null=True, blank=True)
    mensaje_error_sri = models.TextField(null=True, blank=True)

    # --- ARCHIVOS SRI (Requerimiento Normativo) ---
    archivo_xml = models.FileField(upload_to='comprobantes/xml/%Y/%m/', null=True, blank=True, help_text="Archivo XML autorizado por el SRI")
    archivo_pdf = models.FileField(upload_to='comprobantes/pdf/%Y/%m/', null=True, blank=True, help_text="RIDE (PDF) generado")

    class Meta:
        db_table = 'facturas'
        verbose_name = 'Factura'
        ordering = ['-fecha_registro']
        # Evita doble facturación del mismo servicio en el mismo mes
        unique_together = ['servicio', 'anio', 'mes']

    history = HistoricalRecords()


# El detalle se mantiene igual, está perfecto.
class DetalleFacturaModel(models.Model):
    factura = models.ForeignKey(FacturaModel, on_delete=models.CASCADE, related_name='detalles')
    rubro = models.ForeignKey(CatalogoRubroModel, on_delete=models.SET_NULL, null=True, blank=True)
    codigo_principal = models.CharField(max_length=25, null=True, blank=True, help_text="Código Principal/SKU")
    codigo_auxiliar = models.CharField(max_length=25, null=True, blank=True, help_text="Código Auxiliar (Transporte)")
    codigo_impuesto = models.CharField(max_length=4, default="0", help_text="Código IVA (0, 2, 4)")
    concepto = models.CharField(max_length=255)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=4)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'facturas_detalles'

    def __str__(self):
        return f"{self.concepto} - {self.subtotal}"

    history = HistoricalRecords()