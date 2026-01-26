from typing import List, Optional
from dataclasses import dataclass
from datetime import date
from core.domain.evento import Evento, TipoEvento, EstadoEvento
from core.domain.asistencia import Asistencia, EstadoJustificacion
from core.interfaces.repositories import IEventoRepository, IAsistenciaRepository, ISocioRepository

@dataclass
class CrearEventoRequest:
    nombre: str
    tipo: TipoEvento
    fecha: date
    valor_multa: float
    seleccion_socios: str # "TODOS", "BARRIO"
    barrio_id: Optional[int] = None
    lista_socios_ids: Optional[List[int]] = None 

class CrearEventoUseCase:
    def __init__(self, 
                 evento_repo: IEventoRepository, 
                 asistencia_repo: IAsistenciaRepository,
                 socio_repo: ISocioRepository):
        self.evento_repo = evento_repo
        self.asistencia_repo = asistencia_repo
        self.socio_repo = socio_repo

    def execute(self, request: CrearEventoRequest) -> Evento:
        # 1. Crear Evento
        nuevo_evento = Evento(
            id=None,
            nombre=request.nombre,
            tipo=request.tipo,
            fecha=request.fecha,
            valor_multa=request.valor_multa,
            estado=EstadoEvento.BORRADOR
        )
        evento_guardado = self.evento_repo.save(nuevo_evento)

        # 2. Obtener Socios
        socios = []
        if request.seleccion_socios == "TODOS":
            socios = self.socio_repo.list_active()
        elif request.seleccion_socios == "BARRIO":
            if not request.barrio_id:
                raise ValueError("Se requiere barrio_id para selección por barrio")
            socios = self.socio_repo.list_by_barrio(request.barrio_id)
        elif request.seleccion_socios == "MANUAL":
            if request.lista_socios_ids:
                # Optimized: We could fetch them, but for now lets iterate or assume we just need IDs
                # But Asistencia needs Socio ID.
                # If we want to validate they exist, we should fetch them.
                # For MVP, assuming the IDs are valid or handling errors.
                for sid in request.lista_socios_ids:
                    s = self.socio_repo.get_by_id(sid)
                    if s:
                        socios.append(s)
        
        # 3. Crear Asistencias
        asistencias = []
        for socio in socios:
            asistencia = Asistencia(
                id=None,
                evento_id=evento_guardado.id,
                socio_id=socio.id,
                asistio=False,
                estado_justificacion=EstadoJustificacion.SIN_SOLICITUD
            )
            asistencias.append(asistencia)
            
        if asistencias:
            self.asistencia_repo.crear_masivo(asistencias)
            
        return evento_guardado
