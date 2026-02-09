# core/use_cases/gobernanza/resolucion_solicitud_justificacion_use_case.py
from django.db import transaction
from django.utils import timezone
from core.shared.enums import EstadoSolicitud, EstadoCuentaPorCobrar, EstadoAsistencia
from adapters.infrastructure.models import (
    SolicitudJustificacionModel, 
    CuentaPorCobrarModel, 
    AsistenciaModel
)

class ResolucionSolicitudJustificacionUseCase:
    """
    Administrador aprueba o rechaza una justificación.
    EFECTO COLATERAL IMPORTANTE: 
    Si se APRUEBA -> Se busca la deuda (multa) generada y se ANULA saldo pendiente.
    """

    @transaction.atomic
    def ejecutar(self, solicitud_id: int, nuevo_estado: str, observacion_admin: str) -> dict:
        # 1. Obtener Solicitud
        try:
            solicitud = SolicitudJustificacionModel.objects.select_for_update().get(id=solicitud_id)
        except SolicitudJustificacionModel.DoesNotExist:
            raise ValueError("Solicitud no encontrada.")

        if solicitud.estado != EstadoSolicitud.PENDIENTE.value:
            raise ValueError(f"La solicitud ya fue procesada anteriormente ({solicitud.estado}).")

        if nuevo_estado not in [EstadoSolicitud.APROBADA.value, EstadoSolicitud.RECHAZADA.value]:
             raise ValueError("Estado de resolución inválido.")

        # 2. Actualizar Solicitud
        solicitud.estado = nuevo_estado
        solicitud.fecha_resolucion = timezone.now()
        solicitud.observacion_admin = observacion_admin
        solicitud.save()

        resultado = {
            "id": solicitud.id,
            "nuevo_estado": solicitud.estado,
            "accion_financiera": "NINGUNA"
        }

        # 3. Lógica Financiera (Si Aprobada)
        if nuevo_estado == EstadoSolicitud.APROBADA.value:
            asistencia = solicitud.asistencia
            evento = asistencia.evento
            socio = asistencia.socio

            # Cambiar estado asistencia
            asistencia.estado = EstadoAsistencia.JUSTIFICADO.value
            asistencia.save()

            # BUSCAR DEUDA ASOCIADA
            # Referencia usada en procesamiento batch: f"MULTA: {evento.nombre} ({evento.fecha})"
            referencia_base = f"MULTA: {evento.nombre}"
            
            # Buscamos deudas que comiencen con la referencia al evento y sean del socio
            deuda = CuentaPorCobrarModel.objects.filter(
                socio=socio,
                origen_referencia__startswith=referencia_base,
                estado=EstadoCuentaPorCobrar.PENDIENTE.value
            ).first()

            if deuda:
                # ANULAR DEUDA
                deuda.estado = EstadoCuentaPorCobrar.ANULADO.value
                deuda.saldo_pendiente = 0
                deuda.save()
                resultado['accion_financiera'] = f"Deuda {deuda.id} ANULADA por justificación."
            else:
                 resultado['accion_financiera'] = "No se encontró deuda pendiente para anular (quizás ya pagada o no generada)."

        return resultado
