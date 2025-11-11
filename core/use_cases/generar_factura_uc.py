# core/use_cases/generar_factura_uc.py
from core.domain.factura import Factura
from core.interfaces.repositories import (
    IFacturaRepository, ILecturaRepository, IMedidorRepository, ISocioRepository
)
from core.use_cases.dtos import GenerarFacturaDesdeLecturaDTO
from core.shared.exceptions import LecturaNoEncontradaError, MedidorNoEncontradoError

class GenerarFacturaDesdeLecturaUseCase:
    """
    Caso de Uso para generar una Factura a partir de una Lectura registrada.
    """
    def __init__(
        self,
        factura_repo: IFacturaRepository,
        lectura_repo: ILecturaRepository,
        medidor_repo: IMedidorRepository,
        socio_repo: ISocioRepository
    ):
        self.factura_repo = factura_repo
        self.lectura_repo = lectura_repo
        self.medidor_repo = medidor_repo
        self.socio_repo = socio_repo

    def execute(self, input_dto: GenerarFacturaDesdeLecturaDTO) -> Factura:
        # 1. Obtener la lectura base
        lectura = self.lectura_repo.get_by_id(input_dto.lectura_id)
        if not lectura:
            raise LecturaNoEncontradaError("Lectura no encontrada.")

        # 2. Obtener el medidor y el socio
        medidor = self.medidor_repo.get_by_id(lectura.medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError("Medidor asociado a la lectura no encontrado.")
            
        socio = self.socio_repo.get_by_id(medidor.socio_id)
        # Aquí podrías validar si el socio existe, etc.

        # 3. Crear la Entidad Factura
        factura = Factura(
            id=None,
            socio_id=socio.id,
            medidor_id=medidor.id,
            fecha_emision=input_dto.fecha_emision,
            fecha_vencimiento=input_dto.fecha_vencimiento,
            lectura=lectura
        )
        
        # 4. Delegar el CÁLCULO a la Entidad de Dominio
        if medidor.tiene_medidor_fisico:
            factura.calcular_total_con_medidor(lectura.consumo_del_mes_m3)
        else:
            factura.calcular_total_sin_medidor()

        # 5. Guardar la factura
        factura_guardada = self.factura_repo.save(factura)
        
        return factura_guardada