# # core/use_cases/enviar_factura_sri_uc.py

# # Importamos las interfaces que necesita
# from core.interfaces.repositories import IFacturaRepository, ISocioRepository
# from core.interfaces.services import ISRIService, SRIResponse
# # Importamos las excepciones que puede lanzar
# from core.shared.exceptions import FacturaNoEncontradaError, FacturaEstadoError, SocioNoEncontradoError
# # ¡¡¡IMPORTACIÓN AÑADIDA!!!
# from core.shared.enums import EstadoFactura

# class EnviarFacturaSRIUseCase:
#     """
#     Caso de Uso para tomar una factura, firmarla, enviarla al SRI
#     y actualizar su estado.
#     """
#     def __init__(
#         self,
#         factura_repo: IFacturaRepository,
#         socio_repo: ISocioRepository,
#         sri_service: ISRIService
#     ):
#         self.factura_repo = factura_repo
#         self.socio_repo = socio_repo
#         self.sri_service = sri_service # La interfaz que oculta la complejidad

#     def execute(self, factura_id: int) -> SRIResponse:
#         # 1. Obtener la factura
#         factura = self.factura_repo.get_by_id(factura_id)
#         if not factura:
#             raise FacturaNoEncontradaError("Factura no encontrada.")
            
#         # ¡¡¡LÍNEA CORREGIDA!!!
#         # Comparamos Objeto Enum vs Objeto Enum
#         if factura.estado != EstadoFactura.PENDIENTE:
#              raise FacturaEstadoError("Solo se pueden enviar facturas pendientes.")
        
#         # 2. Necesitamos los datos del Socio (Comprador) para el XML
#         socio = self.socio_repo.get_by_id(factura.socio_id)
#         if not socio:
#             raise SocioNoEncontradoError(f"El socio {factura.socio_id} de esta factura no fue encontrado.")

#         # 3. Delegar TODA la lógica del SRI al servicio
#         print(f"Enviando factura {factura.id} (Socio: {socio.cedula}) al SRI...")
#         sri_response = self.sri_service.enviar_factura(factura, socio)
        
#         # 4. Actualizar la factura con la respuesta
#         if sri_response.exito and sri_response.estado == "RECIBIDA":
#             # (En un futuro, aquí cambiarías el estado_sri a "ENVIADA")
#             factura.clave_acceso_sri = sri_response.autorizacion_id
#             factura.estado_sri = sri_response.estado # "RECIBIDA"
#             factura.xml_enviado_sri = sri_response.xml_enviado
#             factura.xml_respuesta_sri = sri_response.xml_respuesta
#             print(f"Factura {factura.id} recibida por el SRI.")
#         else:
#             # Si fue "DEVUELTA" o hubo un "ERROR"
#             factura.estado_sri = sri_response.estado
#             factura.mensaje_sri = sri_response.mensaje_error
#             factura.xml_enviado_sri = sri_response.xml_enviado
#             factura.xml_respuesta_sri = sri_response.xml_respuesta
#             print(f"Factura {factura.id} rechazada por el SRI: {sri_response.mensaje_error}")

#         # 5. Guardar los cambios en la BBDD (el estado_sri, clave_acceso, etc.)
#         self.factura_repo.save(factura)
        
#         return sri_response