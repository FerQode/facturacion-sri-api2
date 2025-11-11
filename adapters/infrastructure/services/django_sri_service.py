# adapters/infrastructure/services/django_sri_service.py

from django.conf import settings
from typing import Optional
import logging
import random
import base64
from datetime import datetime
from lxml import etree

# Librerías de terceros (Asegúrate de instalarlas: pip install zeep xmlsec)
try:
    import zeep
    import xmlsec
except ImportError:
    raise ImportError("Por favor instala 'zeep' y 'xmlsec' (pip install zeep xmlsec)")

# Contratos y Entidades del CORE
from core.interfaces.services import ISRIService, SRIAuthData, SRIResponse
from core.domain.factura import Factura
from core.domain.socio import Socio # ¡Importante! Necesitamos al Socio

# Configura un logger
logger = logging.getLogger(__name__)

class DjangoSRIService(ISIService):
    """
    Implementación del servicio del SRI.
    Lee la configuración (claves, RUC, etc.) desde settings.py.
    """
    def __init__(self):
        # Cargamos las credenciales desde settings.py (donde se leyeron del .env)
        try:
            self.auth = SRIAuthData(
                firma_path=str(settings.SRI_FIRMA_PATH), # Convertir Path a string
                firma_pass=settings.SRI_FIRMA_PASS,
                sri_url_recepcion=settings.SRI_URL_RECEPCION,
                sri_url_autorizacion=settings.SRI_URL_AUTORIZACION
            )
            # Inicializamos los clientes SOAP
            self.soap_client_recepcion = zeep.Client(self.auth.sri_url_recepcion)
            self.soap_client_autorizacion = zeep.Client(self.auth.sri_url_autorizacion)
            logger.info("Clientes SOAP de Recepción y Autorización del SRI inicializados.")
            
        except AttributeError as e:
            logger.error(f"Error: Faltan configuraciones del SRI en settings.py. {e}")
            raise ValueError("Configuración del SRI incompleta. Revisa tu .env y settings.py")
        except Exception as e:
            logger.error(f"Error al inicializar el cliente SOAP de Zeep: {e}")
            raise ConnectionError(f"No se pudo conectar a los WSDL del SRI.")

    # --- HELPER 1: Dígito Verificador (Módulo 11) ---
    def _calcular_digito_verificador_modulo11(self, clave: str) -> str:
        factor = 7
        total = 0
        for digito in clave:
            total += int(digito) * factor
            factor = factor - 1
            if factor == 1:
                factor = 7
        
        resultado = 11 - (total % 11)
        if resultado == 11:
            return "0"
        if resultado == 10:
            return "1"
        return str(resultado)

    # --- HELPER 2: Generador de Clave de Acceso ---
    def _generar_clave_acceso(self, emisor_ruc: str, fecha_emision: datetime.date, nro_factura: str) -> str:
        fecha = fecha_emision.strftime('%d%m%Y')
        tipo_comprobante = "01" # 01 = Factura
        ruc = emisor_ruc
        ambiente = settings.SRI_AMBIENTE
        serie = settings.SRI_SERIE_ESTABLECIMIENTO + settings.SRI_SERIE_PUNTO_EMISION
        secuencial = nro_factura.zfill(9)
        codigo_numerico = "".join(random.choices("0123456789", k=8))
        tipo_emision = "1" # 1 = Normal
        
        clave_sin_dv = (
            fecha + tipo_comprobante + ruc + ambiente + 
            serie + secuencial + codigo_numerico + tipo_emision
        )
        
        digito_verificador = self._calcular_digito_verificador_modulo11(clave_sin_dv)
        clave_acceso = clave_sin_dv + digito_verificador
        
        if len(clave_acceso) != 49:
            raise ValueError(f"Error al generar clave de acceso: longitud incorrecta ({len(clave_acceso)})")
        
        return clave_acceso

    # --- MÉTODO 1: Generación de XML ---
    def _generar_xml_factura(self, factura: Factura, socio: Socio) -> (str, str):
        """
        Función PRIVADA para construir el XML de la factura.
        Usa los datos reales de la Junta de Riego desde settings.
        Devuelve (xml_string, clave_acceso)
        """
        logger.info(f"Generando XML para factura {factura.id}...")
        
        # 1. Obtener datos del Emisor (Junta de Riego) de settings.py
        emisor_ruc = settings.SRI_EMISOR_RUC
        emisor_razon_social = settings.SRI_EMISOR_RAZON_SOCIAL
        emisor_dir_matriz = settings.SRI_EMISOR_DIRECCION_MATRIZ
        emisor_nombre_comercial = settings.SRI_NOMBRE_COMERCIAL
        
        # 2. Generar Clave de Acceso
        nro_factura_secuencial = str(factura.id) # Usamos el ID de la factura como secuencial
        
        clave_acceso = self._generar_clave_acceso(
            emisor_ruc=emisor_ruc,
            fecha_emision=factura.fecha_emision,
            nro_factura=nro_factura_secuencial
        )
        
        # 3. Construir el XML con lxml
        xml_factura = etree.Element("factura", id="comprobante", version="1.1.0") # Versión de factura
        
        info_tributaria = etree.SubElement(xml_factura, "infoTributaria")
        etree.SubElement(info_tributaria, "ambiente").text = settings.SRI_AMBIENTE
        etree.SubElement(info_tributaria, "tipoEmision").text = "1"
        etree.SubElement(info_tributaria, "razonSocial").text = emisor_razon_social
        etree.SubElement(info_tributaria, "nombreComercial").text = emisor_nombre_comercial
        etree.SubElement(info_tributaria, "ruc").text = emisor_ruc
        etree.SubElement(info_tributaria, "claveAcceso").text = clave_acceso
        etree.SubElement(info_tributaria, "codDoc").text = "01"
        etree.SubElement(info_tributaria, "estab").text = settings.SRI_SERIE_ESTABLECIMIENTO
        etree.SubElement(info_tributaria, "ptoEmi").text = settings.SRI_SERIE_PUNTO_EMISION
        etree.SubElement(info_tributaria, "secuencial").text = nro_factura_secuencial.zfill(9)
        etree.SubElement(info_tributaria, "dirMatriz").text = emisor_dir_matriz
        
        info_factura = etree.SubElement(xml_factura, "infoFactura")
        etree.SubElement(info_factura, "fechaEmision").text = factura.fecha_emision.strftime('%d/%m/%Y')
        etree.SubElement(info_factura, "dirEstablecimiento").text = emisor_dir_matriz # Usamos la misma
        # etree.SubElement(info_factura, "contribuyenteEspecial").text = "..." # No aplica
        etree.SubElement(info_factura, "obligadoContabilidad").text = "SI" # Del PDF [cite: 441]
        etree.SubElement(info_factura, "tipoIdentificacionComprador").text = "05" # 05=Cédula
        etree.SubElement(info_factura, "razonSocialComprador").text = socio.nombre_completo()
        etree.SubElement(info_factura, "identificacionComprador").text = socio.cedula
        etree.SubElement(info_factura, "totalSinImpuestos").text = f"{factura.subtotal:.2f}"
        etree.SubElement(info_factura, "totalDescuento").text = "0.00"
        
        total_con_impuestos = etree.SubElement(info_factura, "totalConImpuestos")
        total_impuesto = etree.SubElement(total_con_impuestos, "totalImpuesto")
        etree.SubElement(total_impuesto, "codigo").text = "2" # 2 = IVA
        etree.SubElement(total_impuesto, "codigoPorcentaje").text = "0" # 0 = IVA 0%
        etree.SubElement(total_impuesto, "baseImponible").text = f"{factura.subtotal:.2f}"
        etree.SubElement(total_impuesto, "valor").text = "0.00"
        
        etree.SubElement(info_factura, "propina").text = "0.00"
        etree.SubElement(info_factura, "importeTotal").text = f"{factura.total:.2f}"
        etree.SubElement(info_factura, "moneda").text = "DOLAR"
        
        pagos = etree.SubElement(info_factura, "pagos")
        pago = etree.SubElement(pagos, "pago")
        etree.SubElement(pago, "formaPago").text = "01" # 01 = Sin utilización sistema financiero
        etree.SubElement(pago, "total").text = f"{factura.total:.2f}"

        # Detalles de la Factura
        detalles = etree.SubElement(xml_factura, "detalles")
        for i, detalle_entidad in enumerate(factura.detalles, 1):
            detalle_xml = etree.SubElement(detalles, "detalle")
            etree.SubElement(detalle_xml, "codigoPrincipal").text = str(i) # Usamos un correlativo
            etree.SubElement(detalle_xml, "descripcion").text = detalle_entidad.concepto[:300]
            etree.SubElement(detalle_xml, "cantidad").text = f"{detalle_entidad.cantidad:.2f}"
            etree.SubElement(detalle_xml, "precioUnitario").text = f"{detalle_entidad.precio_unitario:.4f}" # SRI pide más decimales aquí
            etree.SubElement(detalle_xml, "descuento").text = "0.00"
            etree.SubElement(detalle_xml, "precioTotalSinImpuesto").text = f"{detalle_entidad.subtotal:.2f}"
            
            impuestos_detalle = etree.SubElement(detalle_xml, "impuestos")
            impuesto_detalle = etree.SubElement(impuestos_detalle, "impuesto")
            etree.SubElement(impuesto_detalle, "codigo").text = "2" # IVA
            etree.SubElement(impuesto_detalle, "codigoPorcentaje").text = "0" # IVA 0%
            etree.SubElement(impuesto_detalle, "tarifa").text = "0"
            etree.SubElement(impuesto_detalle, "baseImponible").text = f"{detalle_entidad.subtotal:.2f}"
            etree.SubElement(impuesto_detalle, "valor").text = "0.00"

        # Convertir el árbol XML a string
        xml_string = etree.tostring(xml_factura, encoding="UTF-8", xml_declaration=True, pretty_print=True)
        return xml_string.decode("utf-8"), clave_acceso

    # --- MÉTODO 2: Firma Digital ---
    def _firmar_xml(self, xml_string: str) -> str:
        """
        Función PRIVADA para aplicar la firma XAdES-BES (PKCS#12) usando xmlsec.
        """
        logger.info(f"Firmando XML...")
        
        doc = etree.fromstring(xml_string.encode("utf-8"))
        
        signature_node = xmlsec.template.create(
            doc,
            xmlsec.constants.TransformExclC14N,
            xmlsec.constants.TransformRsaSha1
        )
        doc.append(signature_node)
        
        ref = xmlsec.template.add_reference(
            signature_node, 
            xmlsec.constants.TransformSha1
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)

        key_info = xmlsec.template.ensure_key_info(signature_node)
        x509_data = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.add_x509_issuer_serial(x509_data)
        xmlsec.template.add_x509_certificate(x509_data)

        ctx = xmlsec.SignatureContext()
        
        try:
            key = xmlsec.Key.from_file(
                self.auth.firma_path, 
                xmlsec.constants.KeyDataFormatPkcs12, 
                self.auth.firma_pass
            )
            ctx.key = key
        except Exception as e:
            logger.error(f"Error al cargar la firma digital P12: {e}. Revisa la ruta y la contraseña en .env")
            raise IOError("No se pudo cargar la firma digital. Revisa la ruta y la contraseña.")

        ctx.sign(signature_node)
        
        logger.info("XML firmado exitosamente.")
        signed_xml_string = etree.tostring(doc, encoding="UTF-8", xml_declaration=False)
        return signed_xml_string.decode("utf-8")

    # --- MÉTODO 3: Envío al SRI ---
    def _enviar_comprobante_al_sri(self, xml_firmado: str) -> dict:
        """
        Función PRIVADA para enviar el XML al Web Service SOAP de Recepción.
        """
        logger.info("Enviando comprobante al SRI (Recepción)...")
        
        try:
            # 1. Codificar el XML a Base64
            xml_base64 = base64.b64encode(xml_firmado.encode("utf-8")).decode("utf-8")
            
            # 2. Llamar al método 'validarComprobante' del Web Service
            respuesta_soap = self.soap_client_recepcion.service.validarComprobante(xml_base64)
            
            logger.info(f"Respuesta del SRI (Recepción) recibida: {respuesta_soap['estado']}")
            return respuesta_soap

        except zeep.exceptions.Fault as fault:
            logger.error(f"Error SOAP al enviar al SRI: {fault.message}")
            return {"estado": "ERROR_SOAP", "mensaje": fault.message}
        except Exception as e:
            logger.error(f"Error de conexión o timeout con el SRI (Recepción): {e}")
            return {"estado": "ERROR_CONEXION", "mensaje": str(e)}

    # --- MÉTODO 4: Parseo de Respuesta ---
    def _parsear_respuesta_sri(self, respuesta_soap: dict, clave_acceso: str, xml_enviado: str) -> SRIResponse:
        """Convierte la compleja respuesta SOAP en nuestro DTO simple."""
        
        estado = respuesta_soap.get("estado")
        xml_respuesta_str = str(respuesta_soap) # Guardamos la respuesta completa
        
        if estado == "RECIBIDA":
            return SRIResponse(
                exito=True, 
                autorizacion_id=clave_acceso,
                estado=estado, # "RECIBIDA" (significa que está en cola para autorizar)
                mensaje_error=None,
                xml_enviado=xml_enviado,
                xml_respuesta=xml_respuesta_str
            )
        
        if estado == "DEVUELTA":
            try:
                # Intentamos obtener el error específico
                mensaje = respuesta_soap['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['mensaje']
                info_adicional = respuesta_soap['comprobantes']['comprobante'][0]['mensajes']['mensaje'][0]['informacionAdicional']
                error_completo = f"{mensaje} - {info_adicional}"
            except Exception:
                error_completo = xml_respuesta_str # Devolvemos todo si falla el parseo
                
            return SRIResponse(
                exito=False,
                autorizacion_id=clave_acceso,
                estado=estado,
                mensaje_error=error_completo,
                xml_enviado=xml_enviado,
                xml_respuesta=xml_respuesta_str
            )

        # Otros errores (SOAP, Conexión, etc.)
        return SRIResponse(
            exito=False,
            autorizacion_id=clave_acceso,
            estado=estado or "ERROR_DESCONOCIDO",
            mensaje_error=respuesta_soap.get("mensaje", "Error desconocido."),
            xml_enviado=xml_enviado,
            xml_respuesta=xml_respuesta_str
        )
    
    # --- MÉTODOS PÚBLICOS DE LA INTERFAZ ---
    
    def enviar_factura(self, factura: Factura, socio: Socio) -> SRIResponse:
        """Implementación del contrato de la interfaz."""
        try:
            # 1. Generar XML (¡Corregido! Pasamos el socio)
            xml_para_firmar, clave_acceso = self._generar_xml_factura(factura, socio)
            
            # 2. Firmar XML
            xml_firmado = self._firmar_xml(xml_para_firmar)
            
            # 3. Enviar al SRI
            respuesta_soap = self._enviar_comprobante_al_sri(xml_firmado)

            # 4. Interpretar respuesta y guardarla
            return self._parsear_respuesta_sri(respuesta_soap, clave_acceso, xml_firmado)

        except Exception as e:
            logger.error(f"Fallo total en envío al SRI para factura {factura.id}: {e}", exc_info=True)
            return SRIResponse(
                exito=False,
                autorizacion_id=None,
                estado="ERROR_INTERNO",
                mensaje_error=str(e),
                xml_enviado=None,
                xml_respuesta=None
            )

    def consultar_autorizacion(self, clave_acceso: str) -> SRIResponse:
        """
        Consulta el estado de una factura ya enviada (RECIBIDA) 
        usando su claveAcceso.
        """
        logger.info(f"Consultando autorización para clave: {clave_acceso}")
        try:
            # Usamos el cliente de Autorización
            respuesta_soap = self.soap_client_autorizacion.service.autorizacionComprobante(clave_acceso)
            
            # El parseo de la respuesta de autorización es diferente
            estado = respuesta_soap.autorizaciones.autorizacion[0].estado
            if estado == "AUTORIZADO":
                 return SRIResponse(
                    exito=True, 
                    autorizacion_id=clave_acceso,
                    estado=estado, 
                    mensaje_error=None,
                    xml_enviado=None,
                    xml_respuesta=str(respuesta_soap)
                )
            else: # NO AUTORIZADO
                mensaje = respuesta_soap.autorizaciones.autorizacion[0].mensajes.mensaje[0].mensaje
                info_adicional = respuesta_soap.autorizaciones.autorizacion[0].mensajes.mensaje[0].informacionAdicional
                error_completo = f"{mensaje} - {info_adicional}"
                return SRIResponse(
                    exito=False,
                    autorizacion_id=clave_acceso,
                    estado=estado,
                    mensaje_error=error_completo,
                    xml_enviado=None,
                    xml_respuesta=str(respuesta_soap)
                )

        except zeep.exceptions.Fault as fault:
            logger.error(f"Error SOAP al consultar autorización: {fault.message}")
            return SRIResponse(exito=False, autorizacion_id=clave_acceso, estado="ERROR_SOAP", mensaje_error=fault.message, xml_enviado=None, xml_respuesta=None)
        except Exception as e:
            logger.error(f"Error de conexión o timeout (Autorización): {e}", exc_info=True)
            return SRIResponse(exito=False, autorizacion_id=clave_acceso, estado="ERROR_CONEXION", mensaje_error=str(e), xml_enviado=None, xml_respuesta=None)