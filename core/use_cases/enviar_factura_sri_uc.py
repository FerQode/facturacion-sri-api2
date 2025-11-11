# core/use_cases/enviar_factura_sri_uc.py
from core.interfaces.repositories import IFacturaRepository, ISocioRepository
from core.interfaces.services import ISRIService, SRIResponse
from core.shared.exceptions import FacturaNoEncontradaError, FacturaEstadoError

class EnviarFacturaSRIUseCase:
    """
    Caso de Uso para tomar una factura, firmarla, enviarla al SRI
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
        self.sri_service = sri_service # La interfaz que oculta la complejidad

    def execute(self, factura_id: int) -> SRIResponse:
        # 1. Obtener la factura
        factura = self.factura_repo.get_by_id(factura_id)
        if not factura:
            raise FacturaNoEncontradaError("Factura no encontrada.")
            
        if factura.estado != "PENDIENTE":
             raise FacturaEstadoError("Solo se pueden enviar facturas pendientes.")
        
        # (Aquí también buscaríamos al socio para completar datos del SRI)
        # socio = self.socio_repo.get_by_id(factura.socio_id)
        # ...y pasarle al servicio los datos completos que necesita.

        # 2. Delegar TODA la lógica del SRI al servicio
        #    Aquí es donde GenAI te ayudará a implementar ISRIService
        #    para generar XML, firmar y consumir el Web Service SOAP/REST.
        
        print(f"Enviando factura {factura.id} al SRI...")
        sri_response = self.sri_service.enviar_factura(factura)
        
        # 3. Actualizar la factura con la respuesta
        if sri_response.exito and sri_response.estado == "AUTORIZADO":
            factura.clave_acceso_sri = sri_response.autorizacion_id
            factura.estado_sri = "AUTORIZADO"
            print(f"Factura {factura.id} autorizada.")
        else:
            factura.estado_sri = "RECHAZADO"
            factura.mensaje_sri = sri_response.mensaje_error
            print(f"Factura {factura.id} rechazada: {sri_response.mensaje_error}")

        # 4. Guardar los cambios
        self.factura_repo.save(factura)
        
        return sri_response