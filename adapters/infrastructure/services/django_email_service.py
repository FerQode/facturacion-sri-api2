# adapters/infrastructure/services/django_email_service.py
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DjangoEmailService:
    """
    Servicio de Infraestructura para el envío de correos electrónicos.
    Se encarga de adjuntar el XML autorizado.
    """

    def enviar_notificacion_factura(self, email_destinatario, nombre_socio, numero_factura, xml_autorizado):
        """
        Envía la factura autorizada al correo del socio.
        """
        # 1. Validación básica
        if not email_destinatario or '@' not in email_destinatario:
            logger.warning(f"📭 El socio {nombre_socio} no tiene correo válido. No se envía notificación.")
            return False

        try:
            # 2. Configurar Asunto y Mensaje
            asunto = f"Comprobante Electrónico - Factura #{numero_factura}"
            
            mensaje_html = f"""
            <html>
            <body>
                <h2 style="color: #2c3e50;">Estimado(a) {nombre_socio},</h2>
                <p>La <strong>Junta de Agua Potable "El Arbolito"</strong> le informa que su pago ha sido procesado exitosamente.</p>
                <p>Adjunto encontrará su factura electrónica autorizada por el SRI.</p>
                <br>
                <p style="font-size: 12px; color: #7f8c8d;">Este es un mensaje automático, por favor no responder.</p>
            </body>
            </html>
            """

            # 3. Crear el Objeto de Correo
            email = EmailMultiAlternatives(
                subject=asunto,
                body="Su gestor de correo no soporta HTML.", # Mensaje alternativo
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destinatario]
            )
            email.attach_alternative(mensaje_html, "text/html")

            # 4. Adjuntar el XML (Obligatorio)
            if xml_autorizado:
                nombre_archivo = f"factura_{numero_factura}.xml"
                email.attach(nombre_archivo, xml_autorizado, 'application/xml')

            # 5. Enviar
            email.send()
            logger.info(f"📧 Correo enviado exitosamente a {email_destinatario}")
            return True

        except Exception as e:
            logger.error(f"❌ Error enviando correo a {email_destinatario}: {str(e)}")
            # Retornamos False pero NO lanzamos error para no tumbar el cobro
            return False