# core/use_cases/gobernanza/crear_solicitud_justificacion.py
from typing import TypedDict, Optional
from django.db import transaction
from django.core.files.uploadedfile import UploadedFile

from core.shared.enums import EstadoAsistencia, EstadoSolicitud
from adapters.infrastructure.models import AsistenciaModel, SolicitudJustificacionModel

class SolicitudInput(TypedDict):
    asistencia_id: int
    motivo: str
    descripcion: str
    archivo_evidencia: Optional[UploadedFile]

class CrearSolicitudJustificacionUseCase:
    """
    Permite a un socio (o admin) solicitar la justificación de una 'FALTA' o 'ATRASO'.
    Si se aprueba posteriormente, se anulará la multa.
    """

    @transaction.atomic
    def ejecutar(self, data: SolicitudInput) -> dict:
        asistencia_id = data['asistencia_id']
        
        # 1. Validar Asistencia
        try:
            asistencia = AsistenciaModel.objects.select_for_update().get(id=asistencia_id)
        except AsistenciaModel.DoesNotExist:
            raise ValueError(f"Registro de asistencia {asistencia_id} no existe.")

        # Solo se pueden justificar FALTAS o ATRASOS
        if asistencia.estado not in [EstadoAsistencia.FALTA.value, EstadoAsistencia.ATRASO.value]:
            raise ValueError(f"No se puede justificar una asistencia con estado '{asistencia.estado}'. Solo FALTAS o ATRASOS.")

        # Verificar si ya existe una solicitud
        if hasattr(asistencia, 'solicitud_justificacion'):
             solicitud_existente = asistencia.solicitud_justificacion
             if solicitud_existente.estado == EstadoSolicitud.PENDIENTE.value:
                  raise ValueError("Ya existe una solicitud pendiente para esta falta.")
             # Si fue rechazada, ¿permitimos otra? Por ahora asumimos que sí o no según regla de negocio.
             # Bloqueamos para simplificar MVP.
             if solicitud_existente.estado == EstadoSolicitud.RECHAZADA.value:
                 raise ValueError("La justificación anterior fue rechazada. Contacte a secretaría.")

        # 2. Crear Solicitud
        solicitud = SolicitudJustificacionModel.objects.create(
            asistencia=asistencia,
            motivo=data['motivo'],
            descripcion=data['descripcion'],
            archivo_evidencia=data.get('archivo_evidencia'),
            estado=EstadoSolicitud.PENDIENTE.value
        )
        
        # Opcional: Podríamos marcar la asistencia como 'EN_PROCESO_JUSTIFICACION' si existiera ese estado,
        # pero 'FALTA' sigue siendo la verdad hasta que se apruebe.

        return {
            "id": solicitud.id,
            "estado": solicitud.estado,
            "mensaje": "Solicitud creada exitosamente. Pendiente de revisión."
        }
