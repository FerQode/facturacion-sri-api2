# core/use_cases/gobernanza/procesar_justificacion_use_case.py
from core.interfaces.repositories import IAsistenciaRepository, IFacturaRepository
from core.domain.asistencia import EstadoJustificacion
from core.shared.enums import EstadoFactura

class ProcesarJustificacionUseCase:
    def __init__(self, 
                 asistencia_repo: IAsistenciaRepository,
                 factura_repo: IFacturaRepository):
        self.asistencia_repo = asistencia_repo
        self.factura_repo = factura_repo

    def execute(self, asistencia_id: int, decision: str, observacion: str):
        # 1. Obtener Asistencia
        asistencia = self.asistencia_repo.get_by_id(asistencia_id)
        if not asistencia:
            raise ValueError("Asistencia no encontrada")

        # 2. Validar Decisión
        try:
            nuevo_estado = EstadoJustificacion(decision)
        except ValueError:
            raise ValueError(f"Estado de justificación inválido: {decision}")

        # 3. Lógica de Aprobación
        if nuevo_estado == EstadoJustificacion.APROBADA:
            # Si tiene multa generada, intentar anularla
            if asistencia.multa_factura_id:
                factura = self.factura_repo.obtener_por_id(asistencia.multa_factura_id)
                if factura:
                    if factura.estado == EstadoFactura.PAGADA:
                        raise ValueError("No se puede anular la justificación porque la multa YA FUE PAGADA.")
                    
                    if factura.estado == EstadoFactura.PENDIENTE:
                        factura.estado = EstadoFactura.ANULADA
                        self.factura_repo.save(factura)
        
        # 4. Actualizar Asistencia
        asistencia.estado_justificacion = nuevo_estado
        asistencia.observacion = observacion
        self.asistencia_repo.save(asistencia)
