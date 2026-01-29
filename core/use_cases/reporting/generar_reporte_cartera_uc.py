# core/use_cases/reporting/generar_reporte_cartera_uc.py
from typing import List, Dict, Any
from datetime import date
from django.db.models import Sum, Q, F
from django.utils import timezone
from core.interfaces.repositories import IFacturaRepository, ISocioRepository
# Importamos el modelo concreto solo para type hinting si es necesario, 
# pero idealmente deberíamos usar repositorios. 
# Para reportes complejos, a veces es aceptable usar el ORM directo para agregaciones 
# si el repositorio es muy genérico, pero intentaremos mantenerlo limpio.
from adapters.infrastructure.models.factura_model import FacturaModel 
from core.shared.enums import EstadoFactura

class GenerarReporteCarteraUseCase:
    """
    Caso de Uso: Generar Reporte de Cartera Vencida (Aging Report).
    Clasifica la deuda de los socios en:
    - Corriente (Mes actual)
    - Vencida 1-3 Meses
    - Incobrable (> 3 Meses)
    """

    def execute(self) -> List[Dict[str, Any]]:
        """
        Retorna una lista de diccionarios con el resumen de deuda por socio.
        """
        hoy = timezone.now().date()
        
        # 1. Obtener todas las facturas pendientes
        # Nota: Idealmente esto iría en un metría específica del Repositorio,
        # pero para analytics usamos ORM para optimizar agregaciones.
        facturas_pendientes = FacturaModel.objects.filter(
            estado=EstadoFactura.PENDIENTE.value
        ).select_related('socio__barrio', 'medidor')

        reporte = {}

        for factura in facturas_pendientes:
            socio_id = factura.socio.id
            nombre_socio = f"{factura.socio.apellidos} {factura.socio.nombres}"
            
            if socio_id not in reporte:
                reporte[socio_id] = {
                    "socio_id": socio_id,
                    "nombre": nombre_socio,
                    "barrio": factura.socio.barrio.nombre if factura.socio.barrio else "Sin Barrio",
                    "identificacion": factura.socio.identificacion,
                    "total_deuda": 0.00,
                    "corriente": 0.00,      # < 30 días
                    "vencido_1_3": 0.00,    # 30 - 90 días
                    "incobrable": 0.00,     # > 90 días
                    "facturas_pendientes": 0
                }

            # Calcular días de mora
            dias_mora = (hoy - factura.fecha_emision).days
            monto = float(factura.total)

            # Acumular
            reporte[socio_id]["total_deuda"] += monto
            reporte[socio_id]["facturas_pendientes"] += 1

            # Clasificar
            if dias_mora <= 30:
                reporte[socio_id]["corriente"] += monto
            elif 30 < dias_mora <= 90:
                reporte[socio_id]["vencido_1_3"] += monto
            else:
                reporte[socio_id]["incobrable"] += monto

        # Convertir a lista y ordenar por deuda (Mayor a menor)
        lista_reporte = list(reporte.values())
        lista_reporte.sort(key=lambda x: x["total_deuda"], reverse=True)

        return lista_reporte
