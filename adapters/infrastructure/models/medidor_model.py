from django.db import models
from .terreno_model import TerrenoModel

class MedidorModel(models.Model):
    """
    Representa el dispositivo físico instalado en un terreno.
    """
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo/Suspendido'),
        ('DANADO', 'Dañado'),
        ('ROBADO', 'Robado'), # Agregado útil para auditoría
        ('MANTENIMIENTO', 'En Mantenimiento'),
    ]

    id = models.AutoField(primary_key=True)

    # --- CAMBIO APLICADO ---
    # OneToOne: Un terreno solo puede tener UN medidor físico activo.
    terreno = models.OneToOneField(
        TerrenoModel,
        # PROTECCIÓN DE DATOS: Si se borra el terreno, el medidor NO se borra,
        # solo se desvincula (se pone en Null). Así no pierdes inventario.
        on_delete=models.SET_NULL, 
        related_name='medidor',
        null=True,  # Permite que el medidor exista sin estar instalado (Inventario/Dañado)
        blank=True,
        verbose_name="Ubicación (Terreno)"
    )

    codigo = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Código/Serial"
    )
    
    # Datos técnicos
    marca = models.CharField(max_length=50, blank=True, null=True)
    lectura_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Estado del dispositivo
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    
    observacion = models.TextField(null=True, blank=True)
    fecha_instalacion = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'medidores'
        verbose_name = 'Medidor'
        verbose_name_plural = 'Medidores'

    def __str__(self):
        ubicacion = self.terreno.direccion if self.terreno else "EN BODEGA/RETIRADO"
        return f"[{self.codigo}] {self.estado} - {ubicacion}"