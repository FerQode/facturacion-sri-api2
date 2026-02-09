# core/use_cases/servicio/gestionar_corte_servicio.py
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from adapters.infrastructure.models import (
    ServicioModel, OrdenTrabajoModel, CuentaPorCobrarModel, 
    CatalogoRubroModel, MultaModel
)
from core.shared.enums import EstadoCuentaPorCobrar

class ProcesarCortesBatchUseCase:
    """
    Analiza todos los servicios ACTIVOS.
    Si tienen >= 2 planillas vencidas, cambia estado a SUSPENDIDO y genera Orden de Corte.
    """
    
    UMBRAL_MORA_MESES = 2

    @transaction.atomic
    def ejecutar(self) -> dict:
        servicios_activos = ServicioModel.objects.filter(estado='ACTIVO')
        cortes_generados = 0
        ordenes_creadas = []

        # Rubro opcional: Multa por Corte (si aplica)
        rubro_corte = CatalogoRubroModel.objects.filter(tipo='MULTA', nombre__icontains='CORTE').first()

        for servicio in servicios_activos:
            # 1. Calcular Meses en Mora (Planillas vencidas)
            deudas_vencidas = CuentaPorCobrarModel.objects.filter(
                # Asumiendo que Cuenta no tiene FK servicio directo, usamos el Socio.
                # Si un socio tiene multiples servicios, esto contaría todas las deudas del socio.
                # Para MVP v1: 1 Socio = 1 Servicio activo usualmente, o deuda global bloquea todo.
                socio=servicio.socio,
                rubro__tipo__in=['AGUA', 'PLANILLA'], # Ajustar según catálogo
                estado=EstadoCuentaPorCobrar.PENDIENTE.value,
                fecha_vencimiento__lt=timezone.now().date()
            ).count()

            if deudas_vencidas >= self.UMBRAL_MORA_MESES:
                # 2. Transición de Estado
                servicio.estado = 'SUSPENDIDO'
                servicio.save()

                # 3. Generar Orden de Corte
                orden = OrdenTrabajoModel.objects.create(
                    servicio=servicio,
                    tipo='CORTE',
                    estado='PENDIENTE',
                    observacion_tecnico=f"Corte automático por mora ({deudas_vencidas} meses vencidos)."
                )
                ordenes_creadas.append(orden.id)
                cortes_generados += 1
                
                # 4. (Opcional) Generar Deuda por Gestión de Corte
                if rubro_corte:
                    CuentaPorCobrarModel.objects.create(
                        socio=servicio.socio,
                        rubro=rubro_corte,
                        monto_inicial=rubro_corte.valor_unitario,
                        saldo_pendiente=rubro_corte.valor_unitario,
                        fecha_vencimiento=timezone.now().date() + timedelta(days=30),
                        estado=EstadoCuentaPorCobrar.PENDIENTE.value,
                        origen_referencia=f"CORTE_SERVICIO_{servicio.id}_{timezone.now().date()}"
                    )

        return {
            "procesados": servicios_activos.count(),
            "cortes_generados": cortes_generados,
            "ordenes_ids": ordenes_creadas
        }
