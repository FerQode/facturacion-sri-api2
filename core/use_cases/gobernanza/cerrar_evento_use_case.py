# core/use_cases/gobernanza/cerrar_evento_use_case.py
from typing import List
from datetime import date
from decimal import Decimal
from django.db import transaction  # ✅ Seguridad ACID: Todo o nada

from core.domain.asistencia import EstadoJustificacion, EstadoAsistencia
from core.interfaces.repositories import IEventoRepository, IAsistenciaRepository, ISocioRepository
from core.interfaces.services import IEmailService
from core.domain.evento import EstadoEvento
# Nota: Ya no importamos Factura porque no la creamos aquí.

class CerrarEventoYMultarUseCase:
    def __init__(self,
                 evento_repo: IEventoRepository,
                 asistencia_repo: IAsistenciaRepository,
                 # factura_repo eliminado: No es responsabilidad de este caso de uso
                 email_service: IEmailService,
                 socio_repo: ISocioRepository):
        self.evento_repo = evento_repo
        self.asistencia_repo = asistencia_repo
        self.email_service = email_service
        self.socio_repo = socio_repo

    def execute(self, evento_id: int):
        # ✅ TRANSACTION ATOMIC: Si falla algo a la mitad, no se cierra el evento.
        with transaction.atomic():
            # 1. Validar Evento
            evento = self.evento_repo.get_by_id(evento_id)
            if not evento:
                raise ValueError("Evento no encontrado")

            if evento.estado == EstadoEvento.FINALIZADO:
                raise ValueError("El evento ya está finalizado")

            # 2. Cambiar Estado a FINALIZADO
            evento.cerrar_evento()
            self.evento_repo.save(evento)

            # 3. Identificar Ausentes y Generar Deuda (Sin Factura)
            asistencias = self.asistencia_repo.get_by_evento(evento_id)
            socios_multados_ids = []

            for a in asistencias:
                # Lógica: Es ausente si tiene FALTA o se quedó en PENDIENTE
                es_inasistencia = (a.estado == EstadoAsistencia.FALTA or a.estado == EstadoAsistencia.PENDIENTE)
                # Y además NO tiene justificación aprobada
                no_justificado = (a.estado_justificacion != EstadoJustificacion.APROBADA)

                if es_inasistencia and no_justificado:
                    # Forzamos el estado a FALTA en la BD
                    cambio_estado = False
                    if a.estado != EstadoAsistencia.FALTA:
                        a.estado = EstadoAsistencia.FALTA
                        cambio_estado = True
                    
                    # Limpieza: Aseguramos que no tenga ID de factura basura
                    if a.multa_factura_id is not None:
                        a.multa_factura_id = None
                        cambio_estado = True
                    
                    if cambio_estado:
                        self.asistencia_repo.save(a)
                    
                    socios_multados_ids.append(a.socio_id)

            print(f"✅ Evento cerrado exitosamente. {len(socios_multados_ids)} multas registradas pendientes de cobro.")

        # 4. Notificaciones (Fuera de la transacción para no bloquear)
        self._notificar_deudas(socios_multados_ids, evento)

    def _notificar_deudas(self, socios_ids: List[int], evento):
        for socio_id in socios_ids:
            try:
                socio = self.socio_repo.get_by_id(socio_id)
                if socio and socio.email:
                    # Ajuste semántico: Avisamos de deuda pendiente, no de factura.
                    self.email_service.enviar_notificacion_multa(
                        email_destinatario=socio.email,
                        nombre_socio=f"{socio.nombres} {socio.apellidos}",
                        evento_nombre=evento.nombre,
                        valor_multa=evento.valor_multa
                    )
            except Exception as e:
                # Logueamos el error pero no detenemos el proceso
                print(f"⚠️ Error notificando a socio {socio_id}: {str(e)}")
