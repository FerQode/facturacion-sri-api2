from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

# Models
from adapters.infrastructure.models import (
    SocioModel, ServicioModel, TerrenoModel, BarrioModel,
    FacturaModel, CuentaPorCobrarModel, CatalogoRubroModel,
    PagoModel, DetallePagoModel
)
from core.shared.enums import EstadoFactura, MetodoPagoEnum

class Command(BaseCommand):
    help = 'Seeds production DB with a minimal dataset for smoke testing (Idempotent)'

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱 Starting Smoke Test Seed...")
        
        try:
            with transaction.atomic():
                self._seed_rubros()
                socio_deuda = self._seed_socio_con_deuda()
                socio_cero = self._seed_socio_sin_deuda()
                self._seed_pago_pendiente(socio_deuda)
                
                self.stdout.write(self.style.SUCCESS("✅ Smoke Test Dataset Created!"))
                self.stdout.write(f"  - Socio Con Deuda ID: {socio_deuda.id} ({socio_deuda.identificacion})")
                self.stdout.write(f"  - Socio Sin Deuda ID: {socio_cero.id} ({socio_cero.identificacion})")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to seed: {e}"))

    def _seed_rubros(self):
        rubro, _ = CatalogoRubroModel.objects.get_or_create(
            nombre="AGUA POTABLE",
            defaults={'tipo': 'AGUA_POTABLE', 'valor_unitario': 5.00}
        )
        self.rubro_agua = rubro

    def _seed_socio_con_deuda(self):
        # 1. Barrio
        barrio, _ = BarrioModel.objects.get_or_create(nombre="Barrio Central")
        
        # 2. Socio
        socio, created = SocioModel.objects.get_or_create(
            identificacion="1722254391", # smoke_test_user
            defaults={
                'nombres': "Smoke",
                'apellidos': "Test User Deuda",
                'email': "smoke_deuda@test.com",
                'telefono': "0999999999",
                'direccion': "Calle Falsa 123"
            }
        )
        
        # 3. Terreno & Servicio (Required for Factura)
        terreno, _ = TerrenoModel.objects.get_or_create(
            socio=socio,
            direccion="Lote 1",
            barrio=barrio
        )
        servicio, _ = ServicioModel.objects.get_or_create(
            socio=socio,
            terreno=terreno,
            tipo='FIJO', # Tarifa Fija = Easier
            defaults={'estado': 'ACTIVO'}
        )

        # 4. Factura & Deuda (Generar solo si no tiene deuda pendiente)
        deuda_existente = CuentaPorCobrarModel.objects.filter(socio=socio, saldo_pendiente__gt=0).exists()
        
        if not deuda_existente:
            # Crear Factura
            factura = FacturaModel.objects.create(
                socio=socio,
                servicio=servicio,
                fecha_emision=date(2025, 1, 1),
                fecha_vencimiento=date(2025, 2, 1),
                subtotal=Decimal('5.00'),
                total=Decimal('5.00'),
                estado=EstadoFactura.PENDIENTE.value
            )
            
            # Crear CXC
            CuentaPorCobrarModel.objects.create(
                socio=socio,
                factura=factura,
                rubro=self.rubro_agua,
                monto_inicial=Decimal('5.00'),
                saldo_pendiente=Decimal('5.00'),
                fecha_vencimiento=date(2025, 2, 1)
            )
            self.stdout.write(f"    -> Created Deuda for {socio.nombres}")
            
        return socio

    def _seed_socio_sin_deuda(self):
        socio, _ = SocioModel.objects.get_or_create(
            identificacion="1722254399", 
            defaults={
                'nombres': "Smoke",
                'apellidos': "Test User Clean",
                'email': "smoke_clean@test.com"
            }
        )
        # Ensure no pending debt
        CuentaPorCobrarModel.objects.filter(socio=socio).update(saldo_pendiente=0, estado='PAGADA')
        return socio

    def _seed_pago_pendiente(self, socio):
        # Check if already exists payment for this socio to start simple
        pendiente = PagoModel.objects.filter(socio=socio, validado=False).first()
        if not pendiente:
            pago = PagoModel.objects.create(
                socio=socio,
                monto_total=Decimal('5.00'),
                validado=False,
                observacion="Smoke Test Transferencia"
            )
            
            DetallePagoModel.objects.create(
                pago=pago,
                metodo=MetodoPagoEnum.TRANSFERENCIA.value,
                monto=Decimal('5.00'),
                referencia="TRX-SMOKE-123",
                comprobante_imagen=None # Optional for smoke test logic
            )
            self.stdout.write(f"    -> Created Pago Pendiente ID: {pago.id}")
