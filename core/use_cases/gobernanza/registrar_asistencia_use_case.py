# core/use_cases/gobernanza/registrar_asistencia_use_case.py 
from typing import List
from core.interfaces.repositories import IAsistenciaRepository
from core.domain.asistencia import Asistencia

class RegistrarAsistenciaUseCase:
    def __init__(self, asistencia_repo: IAsistenciaRepository):
        self.asistencia_repo = asistencia_repo

    def execute(self, evento_id: int, socios_asistentes_ids: List[int]) -> bool:
        """
        Registra la asistencia de los socios indicados.
        Los que no estén en la lista permanecerán con asistio=False (default).
        """
        # 1. Obtener todas las asistencias del evento
        asistencias_existentes = self.asistencia_repo.get_by_evento(evento_id)
        
        # 2. Iterar y actualizar
        for asistencia in asistencias_existentes:
            if asistencia.socio_id in socios_asistentes_ids:
                if not asistencia.asistio:
                    asistencia.asistio = True
                    self.asistencia_repo.save(asistencia)
            else:
                # Si estaba marcado y ahora no viene en la lista, ¿lo desmarcamos?
                # Regla de negocio típica: La lista enviada es la "Lista de Presentes".
                # Si alguien estaba presente y no está en la lista, se asume error de digitación previo y se corrige.
                if asistencia.asistio:
                    asistencia.asistio = False
                    self.asistencia_repo.save(asistencia)
                    
        return True
