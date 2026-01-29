# core/use_cases/reporting/generar_cierre_caja_uc.py
from typing import Dict, Any, Optional
from datetime import date
from django.db.models import Sum
from django.utils import timezone
from adapters.infrastructure.models.pago_model import PagoModel

class GenerarCierreCajaUseCase:
    """
    Caso de Uso: Generar Cierre de Caja Diario.
    Permite al tesorero ver cuánto ha recaudado en el día (o rango).
    """

    def execute(self, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None) -> Dict[str, Any]:
        if not fecha_inicio:
            fecha_inicio = timezone.now().date()
        if not fecha_fin:
            fecha_fin = fecha_inicio

        # Filtrar Pagos en el rango (considerando fecha_registro)
        # Ajustamos el filtro para capturar todo el día si es DateTime
        pagos = PagoModel.objects.filter(
            fecha_registro__date__range=[fecha_inicio, fecha_fin]
        )

        # Agregaciones
        total_recaudado = pagos.aggregate(Sum('monto'))['monto__sum'] or 0.00
        
        # Desglose por método
        por_metodo = pagos.values('metodo').annotate(total=Sum('monto'))
        
        desglose = {item['metodo']: float(item['total']) for item in por_metodo}

        return {
            "rango": {
                "inicio": fecha_inicio,
                "fin": fecha_fin
            },
            "total_general": float(total_recaudado),
            "desglose_medios": {
                "EFECTIVO": desglose.get("EFECTIVO", 0.00),
                "TRANSFERENCIA": desglose.get("TRANSFERENCIA", 0.00),
                "OTROS": sum(v for k, v in desglose.items() if k not in ["EFECTIVO", "TRANSFERENCIA"])
            },
            "cantidad_transacciones": pagos.count()
        }
