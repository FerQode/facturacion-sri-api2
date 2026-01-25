from decimal import Decimal
from typing import List
from django.db.models import Sum
from core.interfaces.repositories import IPagoRepository
from adapters.infrastructure.models import PagoModel
from core.shared.enums import MetodoPagoEnum

class DjangoPagoRepository(IPagoRepository):

    def obtener_sumatoria_validada(self, factura_id: int) -> float:
        suma = PagoModel.objects.filter(
            factura_id=factura_id,
            metodo=MetodoPagoEnum.TRANSFERENCIA.value,
            validado=True
        ).aggregate(Sum('monto'))
        
        resultado = suma['monto__sum'] or Decimal("0.00")
        return float(resultado)

    def tiene_pagos_pendientes(self, factura_id: int) -> bool:
        return PagoModel.objects.filter(
            factura_id=factura_id,
            metodo=MetodoPagoEnum.TRANSFERENCIA.value,
            validado=False
        ).exists()

    def registrar_pagos(self, factura_id: int, pagos: List[dict]) -> None:
        """
        Registra pagos provenientes de caja (Ventanilla).
        Soporta EFECTIVO y TRANSFERENCIA.
        Si viene transferencia por aquí (Mixto), se asume validada porque el cajero ya revisó.
        """
        # Limpiamos solo pagos que podríamos estar reescribiendo en esta sesión de caja
        # OJO: Si borramos transferencias anteriores validadas por tesorería sería un error.
        # Pero aquí asumimos pagos "nuevos" de esta transacción.
        # Para evitar duplicados en reintentos, podríamos borrar por 'origen' si tuviéramos ese campo.
        # Por ahora, mantenemos la limpieza de EFECTIVO para idempotencia básica,
        # y agregamos las transferencias nuevas.
        
        # Eliminar efectivo previo de esta factura (idempotencia simple)
        PagoModel.objects.filter(
            factura_id=factura_id,
            metodo=MetodoPagoEnum.EFECTIVO.value
        ).delete()
        
        pagos_a_crear = []
        for p in pagos:
            metodo = p.get('metodo')
            monto = Decimal(str(p['monto']))
            referencia = p.get('referencia')
            observacion = p.get('observacion')
            
            if metodo == MetodoPagoEnum.EFECTIVO.value:
                pagos_a_crear.append(PagoModel(
                    factura_id=factura_id,
                    metodo=MetodoPagoEnum.EFECTIVO.value,
                    monto=monto,
                    referencia=None, # Efectivo no tiene ref
                    observacion=observacion,
                    validado=True
                ))
            
            elif metodo == MetodoPagoEnum.TRANSFERENCIA.value:
                # Si es transferencia en Ventanilla (Mixto), nace validada.
                pagos_a_crear.append(PagoModel(
                    factura_id=factura_id,
                    metodo=MetodoPagoEnum.TRANSFERENCIA.value,
                    monto=monto,
                    referencia=referencia,
                    observacion=f"{observacion or ''} (Val. Ventanilla)",
                    validado=True 
                ))

        if pagos_a_crear:
            PagoModel.objects.bulk_create(pagos_a_crear)
