# core/use_cases/billing/process_payment.py
from datetime import timedelta
from decimal import Decimal
from typing import TypedDict, List, Optional
from django.db import transaction, models
from django.utils import timezone
from dataclasses import dataclass

from adapters.infrastructure.models import (
    SocioModel,
    CuentaPorCobrarModel,
    PagoModel,
    DetallePagoModel,
    ServicioModel,
    OrdenTrabajoModel,
    CatalogoRubroModel
)

@dataclass
class AbonoResponse:
    pago_id: int
    monto_abonado: Decimal
    saldo_restante_total: Decimal
    cuentas_afectadas: int
    estado_servicio: str
    mensaje: str

class ProcesarAbonoUseCase:
    """
    Caso de Uso Financiero: Procesar Abono (Pagos Parciales).
    
    Lógica:
    1. FIFO: Imputa el pago a las deudas más antiguas primero.
    2. Atomicidad: Todo o nada.
    3. Concurrencia: Bloqueo de filas (select_for_update) para evitar doble gasto.
    4. Claridad Fiscal: No altera facturas SRI ya emitidas, solo su saldo interno.
    5. Reactivación: Si se paga todo, genera Orden de Reconexión.
    """
    
    @transaction.atomic
    def ejecutar(self, socio_id: int, monto_abono: Decimal, usuario_id: int) -> AbonoResponse:
        # 1. Validaciones Defensivas
        if monto_abono <= Decimal('0.00'):
            raise ValueError("El monto del abono debe ser mayor a 0.")
            
        # 2. Obtener Socio y Deudas con BLOQUEO DE ESCRITURA (SELECT FOR UPDATE)
        # Esto evita que dos cajeros cobren la misma deuda al mismo tiempo.
        try:
            socio = SocioModel.objects.select_for_update().get(id=socio_id)
        except SocioModel.DoesNotExist:
            raise ValueError(f"El socio con ID {socio_id} no existe.")
            
        # Obtener todas las cuentas por cobrar pendientes (Saldo > 0), ordenadas por antigüedad (FIFO)
        deudas_pendientes = CuentaPorCobrarModel.objects.select_for_update().filter(
            socio_id=socio_id,
            saldo_pendiente__gt=Decimal('0.00')
        ).order_by('fecha_emision')
        
        deuda_total = sum(d.saldo_pendiente for d in deudas_pendientes)
        
        # Validación de Overpayment
        if monto_abono > deuda_total:
             raise ValueError(f"El monto ({monto_abono}) excede la deuda total ({deuda_total}). No se aceptan pagos en exceso.")
             
        # 3. Crear Cabecera del Pago (Recibo Interno)
        pago = PagoModel.objects.create(
            socio=socio,
            monto_total=monto_abono,
            # usuario_cobro_id=usuario_id, 
            # fecha_pago=timezone.now(),  # Removed: field does not exist, uses auto_now_add in fecha_registro
            numero_comprobante_interno=self._generar_comprobante_interno()
        )
        
        # 3.1. Registrar Método de Pago (Asumimos EFECTIVO único por ahora para simplificar)
        DetallePagoModel.objects.create(
            pago=pago,
            monto=monto_abono, # El total del abono
            metodo='EFECTIVO' # Por defecto
        )
        
        # 4. Algoritmo de Imputación (Distribution Logic)
        monto_restante_por_asignar = monto_abono
        cuentas_afectadas_count = 0
        
        for cuenta in deudas_pendientes:
            if monto_restante_por_asignar <= Decimal('0.00'):
                break
                
            # Calcular cuánto se puede pagar de esta cuenta específica
            monto_a_pagar = min(cuenta.saldo_pendiente, monto_restante_por_asignar)
            
            # Actualizar Cuenta
            cuenta.saldo_pendiente -= monto_a_pagar
            if cuenta.saldo_pendiente == Decimal('0.00'):
                cuenta.estado = 'PAGADA'
            # Si la cuenta está ligada a una Factura Fiscal, actualizar referencia (si aplica)
            # if cuenta.factura:
            #     cuenta.factura.saldo_pendiente -= monto_a_pagar
            #     cuenta.factura.save()
            
            cuenta.save()
            
            # Nota: No creamos DetallePagoModel aquí porque ese modelo es para "Métodos de Pago" (Tarjeta, Efectivo),
            # no para "Detalle de Imputación". La trazabilidad detallada requeriría una tabla intermedia (PagoDeuda).
            
            monto_restante_por_asignar -= monto_a_pagar
            cuentas_afectadas_count += 1
            
        # 5. Lógica Operativa (Trigger de Reconexión)
        # Buscar servicio asociado al socio
        this_servicio = ServicioModel.objects.filter(socio=socio).first()
        estado_servicio_actual = this_servicio.estado if this_servicio else "N/A"
        mensaje_adicional = ""
        
        # Recalcular deuda total remanente
        nueva_deuda_total = deuda_total - monto_abono
        
        # Validar si aplica reconexión
        # Nota: La deuda debe ser 0.
        if this_servicio and this_servicio.estado == 'SUSPENDIDO' and nueva_deuda_total <= Decimal('0.00'):
            from core.use_cases.servicio.solicitar_reconexion_use_case import SolicitarReconexionUseCase
            try:
                uc_reconexion = SolicitarReconexionUseCase()
                # Ejecutamos la reconexión. Al estar en la misma transacción, 
                # SolicitarReconexion verá que la deuda ya fue saldada (saldo=0) por el loop anterior.
                res_reconexion = uc_reconexion.ejecutar(this_servicio.id)
                
                estado_servicio_actual = res_reconexion['nuevo_estado']
                mensaje_adicional = f" {res_reconexion['mensaje']}"
            except ValueError as e:
                # Si falla la reconexión por alguna razón (ej. validación extra), 
                # no fallamos el pago, solo logueamos o avisamos.
                mensaje_adicional = f" Pago ok, pero error en reconexión: {str(e)}"
            
        return AbonoResponse(
            pago_id=pago.id,
            monto_abonado=monto_abono,
            saldo_restante_total=nueva_deuda_total,
            cuentas_afectadas=cuentas_afectadas_count,
            estado_servicio=estado_servicio_actual,
            mensaje=f"Pago procesado exitosamente.{mensaje_adicional}"
        )

    def _generar_comprobante_interno(self) -> str:
        # Generador simple de secuencial único basado en timestamp
        # En producción idealmente usar una secuencia de BD o Redis
        import time
        return f"REC-{int(time.time()*1000)}"
