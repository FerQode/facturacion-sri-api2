# core/use_cases/lectura_uc.py

from core.domain.lectura import Lectura
from core.interfaces.repositories import ILecturaRepository, IMedidorRepository
from core.use_cases.lectura_dtos import RegistrarLecturaDTO # Importa el DTO nuevo
from core.shared.exceptions import MedidorNoEncontradoError

class RegistrarLecturaUseCase:
    """
    Caso de Uso (Cerebro) para registrar una nueva lectura de medidor.
    """
    def __init__(self, lectura_repo: ILecturaRepository, medidor_repo: IMedidorRepository):
        # Recibimos las INTERFACES (Contratos), no implementaciones.
        self.lectura_repo = lectura_repo
        self.medidor_repo = medidor_repo

    def execute(self, input_dto: RegistrarLecturaDTO) -> Lectura:
        # 1. Validar que el medidor existe
        medidor = self.medidor_repo.get_by_id(input_dto.medidor_id)
        if not medidor or not medidor.esta_activo:
            raise MedidorNoEncontradoError(f"Medidor {input_dto.medidor_id} no existe o está inactivo.")

        # 2. Obtener la última lectura para saber la "anterior"
        ultima_lectura = self.lectura_repo.get_latest_by_medidor(input_dto.medidor_id)
        
        lectura_anterior_m3 = 0
        if ultima_lectura:
            lectura_anterior_m3 = ultima_lectura.lectura_actual_m3

        # 3. Crear la Entidad de Dominio
        nueva_lectura = Lectura(
            id=None,
            medidor_id=input_dto.medidor_id,
            fecha_lectura=input_dto.fecha_lectura,
            lectura_actual_m3=input_dto.lectura_actual_m3,
            lectura_anterior_m3=lectura_anterior_m3
        )
        
        # 4. Usar el repositorio para guardar
        lectura_guardada = self.lectura_repo.save(nueva_lectura)
        
        return lectura_guardada