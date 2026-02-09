# core/use_cases/servicio/completar_orden_trabajo_use_case.py
from django.db import transaction
from django.core.files.uploadedfile import UploadedFile
from adapters.infrastructure.models import (
    OrdenTrabajoModel, ServicioModel, EvidenciaOrdenTrabajoModel
)
from django.utils import timezone

class CompletarOrdenTrabajoUseCase:
    """
    Finaliza una Orden de Trabajo (Corte o Reconexión).
    Requiere evidencia fotográfica (S3).
    """

    @transaction.atomic
    def ejecutar(self, orden_id: int, archivo_evidencia: UploadedFile, observacion: str) -> dict:
        try:
            orden = OrdenTrabajoModel.objects.select_for_update().get(id=orden_id)
        except OrdenTrabajoModel.DoesNotExist:
            raise ValueError("Orden de trabajo no encontrada.")

        if orden.estado != 'PENDIENTE':
             # Permitir re-subir evidencia si está 'EN_PROCESO'? Asumimos flujo simple: PENDIENTE -> COMPLETADA
             if orden.estado == 'COMPLETADA':
                 raise ValueError("La orden ya fue completada anteriormente.")

        servicio = orden.servicio

        # 1. Guardar Evidencia (S3 handled by Model Field)
        evidencia = EvidenciaOrdenTrabajoModel.objects.create(
            orden=orden,
            archivo=archivo_evidencia,
            descripcion=observacion
        )

        # 2. Actualizar Orden
        orden.estado = 'COMPLETADA'
        orden.fecha_ejecucion = timezone.now()
        orden.observacion_tecnico = observacion # Actualizamos con el reporte final
        orden.save()

        # 3. Actualizar Estado del Servicio (Máquina de Estados)
        cambio_estado = False
        estado_anterior = servicio.estado

        if orden.tipo == 'CORTE':
            if servicio.estado == 'ACTIVO': # Validar transición coherente
                servicio.estado = 'SUSPENDIDO'
                cambio_estado = True
            # Si ya estaba suspendido (por script masivo), confirmamos el corte físico.

        elif orden.tipo == 'RECONEXION':
            if servicio.estado == 'PENDIENTE_RECONEXION':
                servicio.estado = 'ACTIVO'
                cambio_estado = True
        
        if cambio_estado:
            servicio.save()

        return {
            "orden_id": orden.id,
            "evidencia_id": evidencia.id,
            "servicio_id": servicio.id,
            "nuevo_estado_servicio": servicio.estado,
            "mensaje": f"Orden completada. Servicio pasó de {estado_anterior} a {servicio.estado}."
        }
