# core/use_cases/servicio/solicitar_reconexion_use_case.py
from django.db import transaction
from adapters.infrastructure.models import (
    ServicioModel, OrdenTrabajoModel, CuentaPorCobrarModel
)
from core.shared.enums import EstadoCuentaPorCobrar

class SolicitarReconexionUseCase:
    """
    Se ejecuta cuando el socio paga TODA su deuda de agua.
    Genera Orden de Reconexión y cambia estado a PENDIENTE_RECONEXION.
    """

    @transaction.atomic
    def ejecutar(self, servicio_id: int) -> dict:
        try:
             servicio = ServicioModel.objects.select_for_update().get(id=servicio_id)
        except ServicioModel.DoesNotExist:
            raise ValueError(f"Servicio {servicio_id} no encontrado.")

        # 1. Verificar Saldo Cero (Doble Check de seguridad)
        deuda_pendiente = CuentaPorCobrarModel.objects.filter(
            socio=servicio.socio,
            rubro__tipo__in=['AGUA', 'PLANILLA', 'MULTA'], # Incluir multas?
            estado=EstadoCuentaPorCobrar.PENDIENTE.value
        ).exists()

        if deuda_pendiente:
            raise ValueError("Aún existe deuda pendiente. No se puede solicitar reconexión.")

        # 2. Verificar Estado Actual
        if servicio.estado != 'SUSPENDIDO':
             # Si ya está activo o en otro estado, no hacemos nada o lanzamos error.
             # Para robustez, si ya está PENDIENTE_RECONEXION, devolvemos éxito idempotente.
             if servicio.estado == 'PENDIENTE_RECONEXION':
                 return {"mensaje": "Ya existe una solicitud en curso.", "orden_id": None}
             
             # Si está ACTIVO, no tiene sentido reconectar.
             if servicio.estado == 'ACTIVO':
                 return {"mensaje": "El servicio ya está activo.", "orden_id": None}

        # 3. Transición de Estado
        servicio.estado = 'PENDIENTE_RECONEXION'
        servicio.save()

        # 4. Generar Orden de Reconexión
        orden = OrdenTrabajoModel.objects.create(
            servicio=servicio,
            tipo='RECONEXION',
            estado='PENDIENTE',
            observacion_tecnico="Pago total de deuda detectado. Proceder a reconexión."
        )

        return {
            "mensaje": "Solicitud de reconexión generada exitosamente.",
            "orden_id": orden.id,
            "nuevo_estado": servicio.estado
        }
