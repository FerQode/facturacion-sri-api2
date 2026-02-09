# smoke_test_governance.py
import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from adapters.infrastructure.models import (
    SocioModel, EventoModel, AsistenciaModel, 
    CatalogoRubroModel, CuentaPorCobrarModel, MultaModel
)
from core.use_cases.gobernanza.procesar_multas_batch_use_case import ProcesarMultasBatchUseCase
from core.shared.enums import EstadoEvento, EstadoAsistencia, TipoEvento

def run_smoke_test():
    print("🚀 Iniciando Smoke Test de Gobernanza...")

    # 1. Setup Data - Socio
    # Ajustamos campos según el modelo real (verificado en paso anterior)
    socio, _ = SocioModel.objects.get_or_create(
        identificacion="9999999999",
        defaults={
            "nombres": "Socio Test",
            "apellidos": "Smoke",
            "email": "test@smoke.com", 
            "telefono": "0999999999",
            "direccion": "Test Address",
            "esta_activo": True
        }
    )
    print(f"✅ Socio: {socio}")

    # 2. Setup Data - Rubro (Vital para el fallback)
    rubro, _ = CatalogoRubroModel.objects.get_or_create(
        nombre="Multa Minga General",
        defaults={
            "tipo": "MULTA",
            "valor_unitario": Decimal("20.00")
        }
    )
    print(f"✅ Rubro MULTA: {rubro}")

    # 3. Crear Evento
    evento = EventoModel.objects.create(
        nombre="Minga Smoke Test",
        tipo=TipoEvento.MINGA.value,
        fecha=date.today(),
        valor_multa=Decimal("10.00"),
        estado=EstadoEvento.PROGRAMADO.value
    )
    print(f"✅ Evento Creado: {evento}")

    # 4. Registrar Asistencia (FALTA)
    AsistenciaModel.objects.create(
        evento=evento,
        socio=socio,
        estado=EstadoAsistencia.FALTA.value
    )
    print(f"✅ Asistencia (FALTA) registrada para: {socio}")

    # 5. Ejecutar Use Case
    print("⚙️ Ejecutando ProcesarMultasBatchUseCase...")
    use_case = ProcesarMultasBatchUseCase()
    try:
        resultado = use_case.ejecutar(evento_id=evento.id)
        print(f"📊 Resultado Use Case: {resultado}")
    except Exception as e:
        print(f"❌ Error ejecutando Use Case: {e}")
        return

    # 6. Verificaciones
    cuenta = CuentaPorCobrarModel.objects.filter(
        socio=socio,
        origen_referencia__contains=f"MULTA_EVENTO_{evento.id}"
    ).first()

    if cuenta:
        print(f"✅ ÉXITO: CuentaPorCobrar creada [ID: {cuenta.id}]")
        print(f"   - Monto: {cuenta.monto_inicial}")
        print(f"   - Rubro: {cuenta.rubro.nombre}")
        print(f"   - Referencia: {cuenta.origen_referencia}")
    else:
        print("❌ FALLO: No se creó la CuentaPorCobrar.")

    multa_log = MultaModel.objects.filter(
        socio=socio,
        motivo__contains=evento.nombre
    ).first()

    if multa_log:
        print(f"✅ ÉXITO: Registro MultaModel creado [ID: {multa_log.id}]")
    else:
        print("❌ FALLO: No se creó el log en MultaModel.")

    # Cleanup (Opcional, para no ensuciar DB de desarrollo, pero útil dejarlo para inspección)
    # evento.delete() 
    # socio.delete()

if __name__ == "__main__":
    run_smoke_test()
