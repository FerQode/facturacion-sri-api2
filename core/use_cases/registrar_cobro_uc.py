# core/use_cases/registrar_cobro_uc.py
from decimal import Decimal
from typing import List, Dict
from django.db import transaction

from core.shared.enums import EstadoFactura, MetodoPagoEnum
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException
# Interfaces (deberías tenerlas definidas o usar los repos directos por ahora)
# Imports de Modelos (Infraestructura directa para simplificar la tesis, 
# en Clean puro usarías Interfaces Repository)
from adapters.infrastructure.models import FacturaModel, PagoModel

class RegistrarCobroUseCase:
    """
    Gestiona el cobro de una factura permitiendo pagos mixtos (Efectivo + Transferencia).
    """

    def ejecutar(self, factura_id: int, lista_pagos: List[Dict]):
        """
        lista_pagos estructura:
        [
            {"metodo": "EFECTIVO", "monto": 5.00},
            {"metodo": "TRANSFERENCIA", "monto": 10.50, "referencia": "123456"}
        ]
        """
        with transaction.atomic(): # Todo o nada
            # 1. Buscar la Factura
            try:
                factura = FacturaModel.objects.select_for_update().get(id=factura_id)
            except FacturaModel.DoesNotExist:
                raise EntityNotFoundException("La factura no existe.")

            # 2. Validar Estado
            if factura.estado == EstadoFactura.PAGADA.value:
                raise BusinessRuleException("Esta factura ya fue pagada anteriormente.")
            
            if factura.estado == EstadoFactura.ANULADA.value:
                raise BusinessRuleException("No se puede cobrar una factura anulada.")

            # 3. Sumar los pagos entrantes
            total_pagado = Decimal("0.00")
            pagos_a_crear = []

            for p in lista_pagos:
                monto = Decimal(str(p['monto']))
                metodo = p['metodo'] # String: EFECTIVO o TRANSFERENCIA
                referencia = p.get('referencia')

                # Validación específica de Transferencia
                if metodo == MetodoPagoEnum.TRANSFERENCIA.value and not referencia:
                    raise BusinessRuleException("Los pagos por transferencia requieren número de comprobante.")

                total_pagado += monto
                
                # Preparamos el objeto para guardar
                pagos_a_crear.append(PagoModel(
                    factura=factura,
                    metodo=metodo,
                    monto=monto,
                    referencia=referencia,
                    observacion=p.get('observacion')
                ))

            # 4. Validar Montos (Tolerancia de 1 centavo por redondeo)
            # En tu caso, deben pagar EXACTO el total.
            diferencia = factura.total - total_pagado
            if abs(diferencia) > Decimal("0.01"):
                raise BusinessRuleException(f"El pago total (${total_pagado}) no coincide con la deuda (${factura.total}). Diferencia: ${diferencia}")

            # 5. Guardar Pagos
            PagoModel.objects.bulk_create(pagos_a_crear)

            # 6. Actualizar Factura
            factura.estado = EstadoFactura.PAGADA.value
            factura.save()

            return {
                "mensaje": "Cobro registrado exitosamente",
                "factura_id": factura.id,
                "nuevo_estado": factura.estado,
                "total_pagado": total_pagado
            }