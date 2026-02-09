# core/use_cases/gobernanza/procesar_multas_batch_use_case.py
from decimal import Decimal
from typing import TypedDict
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
import calendar

from core.shared.enums import EstadoAsistencia, EstadoCuentaPorCobrar
from adapters.infrastructure.models import (
    EventoModel, 
    AsistenciaModel, 
    CuentaPorCobrarModel, 
    MultaModel,
    CatalogoRubroModel
)

class ResumenProcesamiento(TypedDict):
    multas_generadas: int
    monto_total: Decimal
    mensaje: str

class ProcesarMultasBatchUseCase:
    """
    Caso de Uso Batch: Generación de Multas Automáticas.
    Convierte 'FALTAS' en 'DEUDA' (CuentaPorCobrar).
    """

    @transaction.atomic
    def ejecutar(self, evento_id: int) -> ResumenProcesamiento:
        # 1. Validar Evento y Configuración
        try:
            evento = EventoModel.objects.get(id=evento_id)
        except EventoModel.DoesNotExist:
            raise ValueError(f"Evento {evento_id} no existe.")

        # En el modelo real (0001_initial), valor_multa está en el Evento
        valor_multa = evento.valor_multa

        if valor_multa <= Decimal('0.00'):
             raise ValueError(f"El valor de la multa es $0.00. No se pueden generar deudas.")

        # Buscar un Rubro de tipo MULTA para la CxC
        # (El modelo Evento no tiene FK a Rubro, así que buscamos uno genérico o el primero disponible)
        rubro_multa = CatalogoRubroModel.objects.filter(nombre__icontains="MULTA").first()
        if not rubro_multa:
            # Fallback: Buscar por tipo si existiera, o crea uno dummy/error
             rubro_multa = CatalogoRubroModel.objects.filter(tipo='MULTA').first()
        
        # 1. Obtener datos clave del evento (Constantes para todo el batch)
        valor_multa = evento.valor_multa

        # 2. Buscar Rubro para la cuenta por cobrar (Fallback Logic)
        try:
            rubro_multa = CatalogoRubroModel.objects.filter(tipo='MULTA').first()
            if not rubro_multa:
                 # Fallback crítico: buscar OTROS
                rubro_multa = CatalogoRubroModel.objects.filter(tipo='OTROS').first()
                if not rubro_multa:
                    raise ValueError("No existe un Rubro tipo 'MULTA' ni 'OTROS' en el catálogo.")
        except Exception as e:
            raise ValueError(f"Error contable al buscar rubro multa: {str(e)}")

        # 3. Identificar Infractores (FALTA)
        infractores = AsistenciaModel.objects.select_for_update().filter(
            evento=evento,
            estado=EstadoAsistencia.FALTA.value
        )

        count = 0
        total_monto = Decimal('0.00')
        fecha_actual = timezone.now().date()
        
        # Calcular fecha vencimiento (Fin de Mes)
        last_day = calendar.monthrange(fecha_actual.year, fecha_actual.month)[1]
        fecha_vencimiento = date(fecha_actual.year, fecha_actual.month, last_day)

        # 4. Generación Masiva
        for asistencia in infractores:
            socio = asistencia.socio
            
            # Referencia única para evitar duplicados
            referencia_base = f"MULTA: {evento.nombre} ({evento.fecha})"
            
            # Verificar si ya existe deuda
            if CuentaPorCobrarModel.objects.filter(
                socio=socio, 
                origen_referencia__startswith=referencia_base
            ).exists():
                continue # Ya procesado
            
            # A. Registro de Auditoría (Tabla Multas)
            multa_log = MultaModel.objects.create(
                socio=socio,
                motivo=f"Falta a {evento.nombre}",
                valor=valor_multa,
                estado='PENDIENTE'
            )

            # B. Crear Cuenta Por Cobrar
            cuenta = CuentaPorCobrarModel.objects.create(
                socio=asistencia.socio,
                rubro=rubro_multa,  # Usamos el rubro encontrado
                monto_inicial=valor_multa,
                saldo_pendiente=valor_multa,
                fecha_vencimiento=timezone.now().date() + timedelta(days=30),
                estado='PENDIENTE',
                origen_referencia=f"MULTA_EVENTO_{evento.id}"
            )        
            cuenta.estado=EstadoCuentaPorCobrar.PENDIENTE.value
            # Vinculamos la MultaID a la referencia para trazabilidad
            cuenta.origen_referencia=f"{referencia_base} [ID:{multa_log.id}]"
            cuenta.save()

            count += 1
            total_monto += valor_multa

        return {
            "multas_generadas": count,
            "monto_total": total_monto,
            "mensaje": f"Se generaron {count} multas por un total de ${total_monto}."
        }
