import os
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.use_cases.reporting.generar_reporte_cartera_uc import GenerarReporteCarteraUseCase
from core.use_cases.reporting.generar_cierre_caja_uc import GenerarCierreCajaUseCase
from adapters.infrastructure.models.socio_model import SocioModel
from adapters.infrastructure.models.factura_model import FacturaModel

def test_analytics():
    print("--- 🔍 VERIFICANDO ANALYTICS ---")
    
    # 1. Cartera Vencida
    print("\n[TEST] Ejecutando Reporte Cartera Vencida...")
    uc_cartera = GenerarReporteCarteraUseCase()
    resultado_cartera = uc_cartera.execute()
    
    print(f"Total deudores encontrados: {len(resultado_cartera)}")
    if resultado_cartera:
        print("Top 3 Deudores:")
        for doc in resultado_cartera[:3]:
            print(f" - {doc['nombre']}: Total ${doc['total_deuda']} (Vencido >90d: ${doc['incobrable']})")
    else:
        print("✅ No hay deudores (O la BD está vacía).")

    # 2. Cierre de Caja
    print("\n[TEST] Ejecutando Cierre de Caja (Hoy)...")
    uc_caja = GenerarCierreCajaUseCase()
    resultado_caja = uc_caja.execute()
    
    print(f"Rango: {resultado_caja['rango']}")
    print(f"Total Recaudado: ${resultado_caja['total_general']}")
    print(f"Desglose: {resultado_caja['desglose_medios']}")

if __name__ == "__main__":
    test_analytics()
