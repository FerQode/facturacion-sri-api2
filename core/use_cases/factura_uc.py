# core/use_cases/factura_uc.py
import logging
from core.domain.factura import Factura
from core.interfaces.repositories import (
    IFacturaRepository, ILecturaRepository, IMedidorRepository, ISocioRepository
)
from core.interfaces.services import ISRIService, SRIResponse
# --- ¡IMPORTACIONES ACTUALIZADAS! ---
from core.use_cases.factura_dtos import (
    GenerarFacturaDesdeLecturaDTO, 
    ConsultarAutorizacionDTO,
    EnviarFacturaSRIDTO # <-- Añadido
)
from core.shared.exceptions import (
    LecturaNoEncontradaError, 
    MedidorNoEncontradoError, 
    FacturaNoEncontradaError, 
    SocioNoEncontradoError,
    FacturaEstadoError # <-- Añadido
)
from core.shared.enums import EstadoFactura # <-- Añadido

# Configura un logger
logger = logging.getLogger(__name__)

# --- Caso de Uso 1: Generar Factura ---
class GenerarFacturaDesdeLecturaUseCase:
    """
    Caso de Uso (Cerebro) para generar una Factura
    a partir de una Lectura registrada.
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
        lectura = self.lectura_repo.get_by_id(input_dto.lectura_id)
        if not lectura:
            raise LecturaNoEncontradaError("Lectura no encontrada.")

        medidor = self.medidor_repo.get_by_id(lectura.medidor_id)
        if not medidor:
            raise MedidorNoEncontradoError("Medidor asociado a la lectura no encontrado.")
            
        socio = self.socio_repo.get_by_id(medidor.socio_id)
        if not socio:
            raise SocioNoEncontradoError("Socio asociado al medidor no encontrado.")

        factura = Factura(
            id=None,
            socio_id=socio.id,
            medidor_id=medidor.id,
            fecha_emision=input_dto.fecha_emision,
            fecha_vencimiento=input_dto.fecha_vencimiento,
            lectura=lectura
        )
        
        if medidor.tiene_medidor_fisico:
            factura.calcular_total_con_medidor(lectura.consumo_del_mes_m3)
        else:
            factura.calcular_total_sin_medidor()

        factura_guardada = self.factura_repo.save(factura)
        
        logger.info(f"Factura {factura_guardada.id} generada para socio {socio.id}.")
        return factura_guardada

# --- Caso de Uso 2: Consultar Autorización ---
class ConsultarAutorizacionUseCase:
    """
    Caso de Uso (Cerebro) para consultar el estado de autorización de una
    factura en el SRI y actualizar nuestra base de datos local.
    """
    def __init__(self, factura_repo: IFacturaRepository, sri_service: ISRIService):
        self.factura_repo = factura_repo
        self.sri_service = sri_service
        
    def execute(self, input_dto: ConsultarAutorizacionDTO) -> SRIResponse:
        clave_acceso = input_dto.clave_acceso
        
        logger.debug(f"Consultando autorización para clave: {clave_acceso}")
        sri_response = self.sri_service.consultar_autorizacion(clave_acceso)
        
        if sri_response.exito and sri_response.estado == "AUTORIZADO":
            factura_local = self.factura_repo.get_by_clave_acceso(clave_acceso)
            
            if factura_local:
                factura_local.estado_sri = "AUTORIZADO"
                factura_local.xml_respuesta_sri = sri_response.xml_respuesta
                self.factura_repo.save(factura_local)
                logger.info(f"Factura {factura_local.id} actualizada a AUTORIZADO.")
            else:
                logger.warning(f"Factura AUTORIZADA con clave {clave_acceso} no encontrada en la BBDD local.")
            
        return sri_response

# --- ¡CLASE NUEVA AÑADIDA! (Movida desde su antiguo archivo) ---
class EnviarFacturaSRIUseCase:
    """
    Caso de Uso (Cerebro) para tomar una factura, firmarla, enviarla al SRI
    y actualizar su estado.
    """
    def __init__(
        self,
        factura_repo: IFacturaRepository,
        socio_repo: ISocioRepository,
        sri_service: ISRIService
    ):
        self.factura_repo = factura_repo
        self.socio_repo = socio_repo
        self.sri_service = sri_service

    def execute(self, input_dto: EnviarFacturaSRIDTO) -> SRIResponse:
        factura_id = input_dto.factura_id

        # 1. Obtener la factura
        factura = self.factura_repo.get_by_id(factura_id)
        if not factura:
            raise FacturaNoEncontradaError("Factura no encontrada.")
            
        # 2. Validar estado
        if factura.estado != EstadoFactura.PENDIENTE:
             raise FacturaEstadoError("Solo se pueden enviar facturas pendientes.")
        
        # 3. Obtener el Socio (Comprador)
        socio = self.socio_repo.get_by_id(factura.socio_id)
        if not socio:
            raise SocioNoEncontradoError(f"El socio {factura.socio_id} de esta factura no fue encontrado.")

        # 4. Delegar TODA la lógica del SRI al servicio
        logger.info(f"Enviando factura {factura.id} (Socio: {socio.cedula}) al SRI...")
        sri_response = self.sri_service.enviar_factura(factura, socio)
        
        # 5. Actualizar la factura con la respuesta
        if sri_response.exito and sri_response.estado == "RECIBIDA":
            factura.clave_acceso_sri = sri_response.autorizacion_id
            factura.estado_sri = sri_response.estado # "RECIBIDA"
            logger.info(f"Factura {factura.id} recibida por el SRI.")
        else:
            # Si fue "DEVUELTA" o hubo un "ERROR"
            factura.estado_sri = sri_response.estado
            factura.mensaje_sri = sri_response.mensaje_error
            logger.warning(f"Factura {factura.id} rechazada por el SRI: {sri_response.mensaje_error}")

        # 6. Guardar los cambios en la BBDD
        factura.xml_enviado_sri = sri_response.xml_enviado
        factura.xml_respuesta_sri = sri_response.xml_respuesta
        self.factura_repo.save(factura)
        
        return sri_response