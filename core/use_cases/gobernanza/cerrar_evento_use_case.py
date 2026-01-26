# core/use_cases/gobernanza/cerrar_evento_use_case.py
from typing import List
from datetime import date
from decimal import Decimal
from core.interfaces.repositories import IEventoRepository, IAsistenciaRepository, IFacturaRepository, ISocioRepository
from core.interfaces.services import IEmailService
from core.domain.evento import EstadoEvento
from core.domain.factura import Factura
from core.domain.asistencia import EstadoJustificacion

class CerrarEventoYMultarUseCase:
    def __init__(self, 
                 evento_repo: IEventoRepository, 
                 asistencia_repo: IAsistenciaRepository,
                 factura_repo: IFacturaRepository,
                 email_service: IEmailService,
                 socio_repo: ISocioRepository):
        self.evento_repo = evento_repo
        self.asistencia_repo = asistencia_repo
        self.factura_repo = factura_repo
        self.email_service = email_service
        self.socio_repo = socio_repo

    def execute(self, evento_id: int):
        # 1. Validar Evento
        evento = self.evento_repo.get_by_id(evento_id)
        if not evento:
            raise ValueError("Evento no encontrado")
        
        if evento.estado == EstadoEvento.FINALIZADO:
            raise ValueError("El evento ya está finalizado")

        # 2. Cambiar Estado
        evento.cerrar_evento()
        self.evento_repo.save(evento)

        # 3. Identificar Ausentes
        asistencias = self.asistencia_repo.get_by_evento(evento_id)
        
        ausentes = [
            a for a in asistencias 
            if not a.asistio and a.estado_justificacion != EstadoJustificacion.APROBADA
        ]

        # 4. Generar Multas (Facturas)
        for asistencia in ausentes:
            socio = self.socio_repo.get_by_id(asistencia.socio_id)
            if not socio:
                continue

            # Crear Factura
            # Nota: Factura completa requiere muchos campos. Simplificamos para el caso de multa.
            nueva_factura = Factura(
                id=None,
                socio_id=socio.id,
                medidor_id=None,
                fecha_emision=date.today(),
                fecha_vencimiento=date.today(), # Vence hoy mismo o configurar política
                anio=date.today().year,
                mes=date.today().month
            )
            
            # Agregar detalle de multa
            nueva_factura.agregar_multa(f"Inasistencia a {evento.nombre}", Decimal(evento.valor_multa))
            
            # Persistir Factura
            factura_guardada = self.factura_repo.save(nueva_factura)
            
            # Actualizar Asistencia con ID de multa
            asistencia.multa_factura_id = factura_guardada.id
            self.asistencia_repo.save(asistencia)

            # 5. Notificar
            if socio.email:
                self.email_service.enviar_notificacion_multa(
                    email_destinatario=socio.email,
                    nombre_socio=f"{socio.nombres} {socio.apellidos}",
                    evento_nombre=evento.nombre,
                    valor_multa=evento.valor_multa
                )
