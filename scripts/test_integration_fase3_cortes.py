import os
import django
from decimal import Decimal
from datetime import date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from adapters.infrastructure.models import (
    SocioModel, ServicioModel, CuentaPorCobrarModel, 
    CatalogoRubroModel, OrdenTrabajoModel, EvidenciaOrdenTrabajoModel,
    BarrioModel, TerrenoModel
)
from core.use_cases.servicio.gestionar_corte_servicio import ProcesarCortesBatchUseCase
from core.use_cases.billing.process_payment import ProcesarAbonoUseCase
from core.use_cases.servicio.completar_orden_trabajo_use_case import CompletarOrdenTrabajoUseCase

def run_test_fase_3():
    print("Iniciando Test Fase 3: Cortes y Reconexión...")

    # 1. Setup Data
    rubro_agua, _ = CatalogoRubroModel.objects.get_or_create(
        nombre="Agua Potable Test",
        defaults={"tipo": "AGUA", "valor_unitario": Decimal("10.00")}
    )

    socio, _ = SocioModel.objects.get_or_create(
        identificacion="9999999999",
        defaults={
            "nombres": "Socio Moroso",
            "apellidos": "Test",
            "email": "moroso@test.com",
            "telefono": "0999999999",
            "direccion": "Calle Mora",
            "esta_activo": True
        }
    )

    barrio, _ = BarrioModel.objects.get_or_create(nombre="Barrio Test")
    
    terreno, _ = TerrenoModel.objects.get_or_create(
        socio=socio,
        barrio=barrio,
        defaults={"direccion": "Lote Test 123"}
    )

    servicio, _ = ServicioModel.objects.get_or_create(
        socio=socio,
        terreno=terreno,
        defaults={"tipo": "FIJO", "estado": "ACTIVO"}
    )
    # Reset estado
    servicio.estado = "ACTIVO"
    servicio.save()

    # 2. Generar Deuda (2 Meses) para simular mora
    print("Generando Deuda de 2 Meses...")
    CuentaPorCobrarModel.objects.create(
        socio=socio,
        rubro=rubro_agua,
        monto_inicial=Decimal("10.00"),
        saldo_pendiente=Decimal("10.00"),
        fecha_emision=date.today() - timedelta(days=65), # Hace 2 meses
        fecha_vencimiento=date.today() - timedelta(days=35),
        estado='PENDIENTE',
        origen_referencia="PLANILLA_TEST_1"
    )
    CuentaPorCobrarModel.objects.create(
        socio=socio,
        rubro=rubro_agua,
        monto_inicial=Decimal("10.00"),
        saldo_pendiente=Decimal("10.00"),
        fecha_emision=date.today() - timedelta(days=35), # Hace 1 mes
        fecha_vencimiento=date.today() - timedelta(days=5),
        estado='PENDIENTE',
        origen_referencia="PLANILLA_TEST_2"
    )

    # 3. Ejecutar Proceso de Cortes (Simulando Celery)
    print("Ejecutando ProcesarCortesBatchUseCase...")
    uc_cortes = ProcesarCortesBatchUseCase()
    res_cortes = uc_cortes.ejecutar()
    print(f"Resultado Cortes: {res_cortes}")

    servicio.refresh_from_db()
    if servicio.estado != 'SUSPENDIDO':
        print(f"FALLO: El servicio debería estar SUSPENDIDO. Estado actual: {servicio.estado}")
        return

    orden_corte = OrdenTrabajoModel.objects.filter(servicio=servicio, tipo='CORTE', estado='PENDIENTE').first()
    if not orden_corte:
        print("FALLO: No se generó Orden de Corte.")
        return
    print(f"Servicio SUSPENDIDO y Orden de Corte generada (ID: {orden_corte.id})")

    # 4. Simular Completar Orden de Corte (Fontanero va y corta)
    print("Completando Orden de Corte (Subida de Evidencia)...")
    uc_completar = CompletarOrdenTrabajoUseCase()
    fake_file = SimpleUploadedFile("evidencia_corte.txt", b"foto_corte_simulada")
    
    uc_completar.ejecutar(orden_corte.id, fake_file, "Corte ejecutado. Medidor precintado.")
    orden_corte.refresh_from_db()
    if orden_corte.estado != 'COMPLETADA':
        print("FALLO: La orden de corte no se completó.")
        return
    print("Orden de Corte COMPLETADA.")

    # 5. Pagar Deuda Total (Trigger Reconexión)
    print("Pagando Deuda Total...")
    uc_pago = ProcesarAbonoUseCase()
    # Deuda total es 20.00. Pagamos 20.00.
    res_pago = uc_pago.ejecutar(socio.id, Decimal("20.00"), usuario_id=1)
    
    servicio.refresh_from_db()
    print(f"Estado Post-Pago: {servicio.estado}")
    
    if servicio.estado != 'PENDIENTE_RECONEXION':
        print(f"FALLO: El servicio debería estar PENDIENTE_RECONEXION. Estado: {servicio.estado}")
        return

    orden_rex = OrdenTrabajoModel.objects.filter(servicio=servicio, tipo='RECONEXION', estado='PENDIENTE').first()
    if not orden_rex:
        print("FALLO: No se generó Orden de Reconexión.")
        return
    print(f"Servicio PENDIENTE_RECONEXION y Orden de Reconexión generada (ID: {orden_rex.id})")

    # 6. Completar Reconexión
    print("Completando Reconexión...")
    fake_file_rex = SimpleUploadedFile("evidencia_rex.txt", b"foto_reconexion_simulada")
    uc_completar.ejecutar(orden_rex.id, fake_file_rex, "Servicio restablecido.")
    
    servicio.refresh_from_db()
    if servicio.estado != 'ACTIVO':
        print(f"FALLO: El servicio debería estar ACTIVO. Estado: {servicio.estado}")
        return

    print("PRUEBA EXITOSA: Ciclo completo (Corte -> Pago -> Reconexión) verificado.")

if __name__ == "__main__":
    run_test_fase_3()
