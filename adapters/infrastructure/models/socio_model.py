# adapters/infrastructure/models/socio_model.py
from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User
from core.shared.enums import RolUsuario, ModalidadCobro
from .barrio_model import BarrioModel

class SocioModel(models.Model):
    ROL_CHOICES = [(rol.value, rol.name) for rol in RolUsuario]

    class TipoIdentificacion(models.TextChoices):
        CEDULA = 'C', 'Cédula'
        RUC = 'R', 'RUC'
        PASAPORTE = 'P', 'Pasaporte'

    id = models.AutoField(primary_key=True)
    identificacion = models.CharField(max_length=13, unique=True, verbose_name="Identificación")
    tipo_identificacion = models.CharField(
        max_length=1,
        choices=TipoIdentificacion.choices,
        default=TipoIdentificacion.CEDULA,
        verbose_name="Tipo de Identificación"
    )

    # --- LÓGICA HÍBRIDA (MEDIDOR vs TARIFA FIJA) ---
    modalidad_cobro = models.CharField(
        max_length=20,
        choices=[(m.value, m.name) for m in ModalidadCobro],
        default=ModalidadCobro.MEDIDOR.value,
        verbose_name="Modalidad de Cobro"
    )
    # -----------------------------------------------

    # --- BANDERAS SOCIALES Y LEGALES ---
    es_tercera_edad = models.BooleanField(default=False, verbose_name="Es Tercera Edad")
    tiene_discapacidad = models.BooleanField(default=False, verbose_name="Tiene Discapacidad")
    en_litigio = models.BooleanField(default=False, verbose_name="En Litigio (Suspende Multas)")
    # -----------------------------------

    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, null=True, blank=True)
    email_notificacion = models.EmailField(max_length=254, null=True, blank=True, verbose_name="Email para Facturación")
    telefono = models.CharField(max_length=20, null=True, blank=True)
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento", null=True, blank=True) # Added to match DB
    
    # --- CORRECCIÓN DE ESTANDARIZACIÓN ---
    # Renombramos 'barrio_domicilio' a 'barrio' para que coincida con
    # la lógica de 'barrio_id' que usamos en el resto del sistema.
    barrio = models.ForeignKey(
        BarrioModel, 
        on_delete=models.PROTECT, 
        related_name='residentes',
        null=True,     
        blank=True,
        verbose_name="Barrio de Domicilio"
    )
    # -------------------------------------
    
    direccion = models.CharField(max_length=200, null=True, blank=True, help_text="Referencia exacta del domicilio")

    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default=RolUsuario.SOCIO.value)
    esta_activo = models.BooleanField(default=True)

    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='perfil_socio'
    )

    class Meta:
        db_table = 'socios'
        verbose_name = 'Socio'
        verbose_name_plural = 'Socios'

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.identificacion})"

    history = HistoricalRecords()