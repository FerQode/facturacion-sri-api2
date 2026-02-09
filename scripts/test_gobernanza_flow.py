import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from adapters.infrastructure.models import (
    SocioModel, EventoModel, AsistenciaModel, CatalogoRubroModel, 
    CuentaPorCobrarModel, BarrioModel
)
from core.shared.enums import TipoEvento, EstadoEvento, EstadoAsistencia, TipoRubro
from core.use_cases.gobernanza.registrar_asistencia_use_case import RegistrarAsistenciaUseCase
from core.use_cases.gobernanza.procesar_multas_batch_use_case import ProcesarMultasBatchUseCase

def run_test():
    print("--- 🧪 INICIANDO SMOKE TEST DE GOBERNANZA ---")

    # 1. Setup Datos Maestros
    print("1. Creando Datos Maestros (Barrio, Rubro, Socios)...")
    barrio, _ = BarrioModel.objects.get_or_create(nombre="Barrio Test")
    
    rubro_multa, _ = CatalogoRubroModel.objects.get_or_create(
        nombre="MULTA MINGA TEST",
        defaults={
            'tipo': TipoRubro.MULTA.value,
            'valor_unitario': Decimal('5.00'),
            'iva': False,
            'activo': True
        }
    )

    socio1, _ = SocioModel.objects.get_or_create(identificacion="9999999991", defaults={'nombres': 'Socio', 'apellidos': 'Cumplido', 'barrio': barrio})
    socio2, _ = SocioModel.objects.get_or_create(identificacion="9999999992", defaults={'nombres': 'Socio', 'apellidos': 'Infractor', 'barrio': barrio})

    # 2. Crear Evento
    print("2. Creando Evento...")
    evento = EventoModel.objects.create(
        nombre="Minga de Prueba",
        tipo=TipoEvento.MINGA.value,
        fecha=timezone.now().date() + timedelta(days=1),
        valor_multa=Decimal('5.00'),
        estado=EstadoEvento.PROGRAMADO.value
    )
    print(f"   Evento creado: {evento}")

    # 3. Registrar Asistencia
    print("3. Ejecutando RegistrarAsistenciaUseCase...")
    use_case_asistencia = RegistrarAsistenciaUseCase()
    resultado_asistencia = use_case_asistencia.ejecutar(
        evento_id=evento.id,
        asistencias=[
            {'socio_id': socio1.id, 'estado': EstadoAsistencia.ASISTIO.value, 'observacion': 'Llegó puntual'},
            {'socio_id': socio2.id, 'estado': EstadoAsistencia.FALTA.value, 'observacion': 'No justificó'}
        ]
    )
    print(f"   Resultado Asistencia: {resultado_asistencia}")
    
    # Validar cambio de estado del evento
    evento.refresh_from_db()
    if evento.estado == EstadoEvento.REALIZADO.value:
        print("   ✅ Evento pasó a REALIZADO correctamente.")
    else:
        print(f"   ❌ ERROR: Evento no cambió de estado. Estado actual: {evento.estado}")

    # 4. Procesar Multas
    print("4. Ejecutando ProcesarMultasBatchUseCase...")
    use_case_multas = ProcesarMultasBatchUseCase()
    resultado_multas = use_case_multas.ejecutar(evento_id=evento.id)
    print(f"   Resultado Multas: {resultado_multas}")

    # 5. Verificaciones Finales
    print("5. Verificaciones Finales...")
    
    # Verificar Deuda Socio 2
    # Buscamos por la referencia generada
    referencia_esperada = f"MULTA: {evento.nombre} ({evento.fecha})"
    deuda = CuentaPorCobrarModel.objects.filter(
        socio=socio2, 
        origen_referencia__startswith=referencia_esperada
    ).last()
    
    if deuda:
        print(f"   ✅ Deuda generada para Socio Infractor: ${deuda.saldo_pendiente} - Ref: {deuda.origen_referencia}")
    else:
        print(f"   ❌ ERROR: No se generó deuda para el infractor. Ref buscada: {referencia_esperada}")

    # Verificar NO Deuda Socio 1
    deuda_cumplido = CuentaPorCobrarModel.objects.filter(socio=socio1, origen_referencia__startswith=referencia_esperada).exists()
    if not deuda_cumplido:
        print("   ✅ Socio Cumplido NO tiene deuda.")
    else:
        print("   ❌ ERROR: Se generó deuda indebida al socio cumplido.")

    print("--- 🏁 TEST COMPLETADO ---")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"🔥 CRASH: {e}")
