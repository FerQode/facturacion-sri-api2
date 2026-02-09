# core/use_cases/gobernanza/registrar_asistencia_use_case.py
from typing import List, TypedDict
from django.db import transaction
from django.utils import timezone
from core.shared.enums import EstadoEvento, EstadoAsistencia
from adapters.infrastructure.models import EventoModel, AsistenciaModel, SocioModel

class AsistenciaInput(TypedDict):
    socio_id: int
    estado: str  # ASISTIO, FALTA, ATRASO, ETC.
    observacion: str

class RegistrarAsistenciaUseCase:
    """
    Caso de Uso: Registrar Asistencia a Mingas/Asambleas.
    Soporta carga masiva (Bulk) desde la App Móvil.
    """

    @transaction.atomic
    def ejecutar(self, evento_id: int, asistencias: List[AsistenciaInput]) -> dict:
        # 1. Validar Evento
        try:
            evento = EventoModel.objects.select_for_update().get(id=evento_id)
        except EventoModel.DoesNotExist:
            raise ValueError(f"Evento {evento_id} no existe.")

        if evento.estado == EstadoEvento.CANCELADO.value:
            raise ValueError(f"No se puede registrar asistencia en un evento CANCELADO.")
            
        # 2. Procesar Lista
        procesados = 0
        actualizados = 0
        
        for item in asistencias:
            socio_id = item['socio_id']
            nuevo_estado = item['estado']
            observacion = item.get('observacion', '')

            # Validar estado permitido
            if nuevo_estado not in [e.value for e in EstadoAsistencia]:
                raise ValueError(f"Estado de asistencia inválido: {nuevo_estado}")

            # Upsert (Crear o Actualizar)
            # Usamos update_or_create para manejar re-envíos sin error
            asistencia, created = AsistenciaModel.objects.update_or_create(
                evento=evento,
                socio_id=socio_id,
                defaults={
                    'estado': nuevo_estado,
                    'observacion': observacion,
                    'observacion': observacion
                }
            )
            
            if created:
                procesados += 1
            else:
                actualizados += 1

        # 3. Actualizar Estado del Evento (Si primera vez)
        if evento.estado == EstadoEvento.PROGRAMADO.value and (procesados + actualizados) > 0:
            evento.estado = EstadoEvento.REALIZADO.value # O EN_CURSO si quisiéramos
            evento.save()

        return {
            "mensaje": "Asistencia registrada correctamente.",
            "nuevos": procesados,
            "actualizados": actualizados,
            "total_asistentes": evento.asistencias.count()
        }
