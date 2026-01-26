# adapters/infrastructure/services/django_email_service.py
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
from core.interfaces.services import IEmailService

logger = logging.getLogger(__name__)

class DjangoEmailService(IEmailService):
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

    def enviar_notificacion_multa(self, email_destinatario, nombre_socio, evento_nombre, valor_multa):
        if not email_destinatario or '@' not in email_destinatario:
            logger.warning(f"📭 El socio {nombre_socio} no tiene correo válido. No se envía notificación de multa.")
            return False
            
        try:
            asunto = f"Notificación de Multa - {evento_nombre}"
            mensaje_html = f"""
            <html>
            <body>
                <h2 style="color: #c0392b;">Estimado(a) {nombre_socio},</h2>
                <p>La <strong>Junta de Agua Potable</strong> le informa que se ha generado una multa por inasistencia al evento: <strong>{evento_nombre}</strong>.</p>
                <p>Valor de la multa: <strong>${valor_multa:.2f}</strong></p>
                <p>Por favor, acérquese a cancelar o presente su justificación lo antes posible.</p>
            </body>
            </html>
            """
            
            email = EmailMultiAlternatives(
                subject=asunto,
                body=f"Multa generada por inasistencia a {evento_nombre}. Valor: ${valor_multa}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_destinatario]
            )
            email.attach_alternative(mensaje_html, "text/html")
            email.send()
            logger.info(f"📧 Notificación de multa enviada a {email_destinatario}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de multa a {email_destinatario}: {str(e)}")
            return False