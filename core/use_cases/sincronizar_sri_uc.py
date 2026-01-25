from core.interfaces.repositories import IFacturaRepository
from core.interfaces.services import ISRIService, IEmailService
from core.shared.exceptions import EntityNotFoundException
from core.domain.factura import EstadoFactura
from datetime import datetime

class SincronizarFacturaSRIUseCase:
    """
    Caso de Uso Exclusivo para Sincronizar/Consultar estado SRI.
    NO realiza cobros, solo verifica y actualiza el estado de la factura.
    Ideal para reintentos o polling de facturas "En Procesamiento".
    """
    def __init__(
        self, 
        factura_repo: IFacturaRepository, 
        sri_service: ISRIService,
        email_service: IEmailService
    ):
        self.factura_repo = factura_repo
        self.sri_service = sri_service
        self.email_service = email_service

    def ejecutar(self, factura_id: int) -> dict:
        # 1. Obtener Factura
        factura = self.factura_repo.obtener_por_id(factura_id)
        if not factura:
            raise EntityNotFoundException(f"Factura {factura_id} no encontrada.")

        # 2. Validar Estado Local
        # Si ya está autorizada, no hacemos nada (Idempotencia)
        if factura.estado_sri == "AUTORIZADO":
            return {
                "estado": "AUTORIZADO",
                "mensaje": "La factura ya estaba autorizada previamente.",
                "clave_acceso": factura.sri_clave_acceso
            }

        # 3. Verificar si tiene clave de acceso para consultar
        clave = factura.sri_clave_acceso
        if not clave:
            # Si no tiene clave, no se ha enviado nunca.
            # Podríamos intentar enviarla desde cero si es lo que se desea,
            # pero este UC es de "Sincronización". 
            # Si el usuario quiere "Enviar", debería ser otro flujo o este mismo inteligente.
            # Para este MVP, si no tiene clave, generamos y enviamos.
            
            # Generar Clave (sin RUC, servicio encapsulado)
            clave = self.sri_service.generar_clave_acceso(factura.fecha_emision, str(factura.id))
            factura.sri_clave_acceso = clave
            self.factura_repo.guardar(factura)

            # Intentar Enviar (Primer Intento o Reintento desde cero)
            # Necesitamos el socio. Asumimos que viene cargado en factura.socio_obj (ver RegistrarCobroUC)
            socio = getattr(factura, 'socio_obj', None)
            if not socio:
                 return {"estado": "ERROR", "mensaje": "Datos del socio no disponibles."}
            
            respuesta = self.sri_service.enviar_factura(factura, socio)
        else:
            # 4. Si YA tiene clave (ej. estaba En Procesamiento), CONSULTAMOS estado
            respuesta = self.sri_service.consultar_autorizacion(clave)
            
            # Si la consulta dice "NO_ENCONTRADO" (el SRI nunca la recibió o la borró),
            # entonces intentamos ENVIAR de nuevo.
            if respuesta.estado == "NO_ENCONTRADO" or respuesta.estado == "No existe":
                 socio = getattr(factura, 'socio_obj', None)
                 if socio:
                    respuesta = self.sri_service.enviar_factura(factura, socio)

        # 5. Procesar Respuesta (Común)
        factura.estado_sri = respuesta.estado
        if respuesta.exito:
             factura.estado_sri = "AUTORIZADO"
             factura.sri_xml_autorizado = respuesta.xml_respuesta
             factura.sri_fecha_autorizacion = datetime.now()
             
             # Notificar
             socio = getattr(factura, 'socio_obj', None)
             if socio and socio.email:
                 self.email_service.enviar_notificacion_factura(
                     socio.email, 
                     f"{socio.nombres} {socio.apellidos}", 
                     factura.id, 
                     respuesta.xml_respuesta
                )
        else:
            factura.sri_mensaje_error = respuesta.mensaje_error

        # 6. Guardar Cambios
        self.factura_repo.guardar(factura)

        return {
            "estado": factura.estado_sri,
            "mensaje": factura.sri_mensaje_error or "Proceso exitoso",
            "clave_acceso": factura.sri_clave_acceso,
            "xml_respuesta": respuesta.xml_respuesta
        }
