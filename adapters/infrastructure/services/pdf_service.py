# adapters/infrastructure/services/pdf_service.py
import logging
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.dateformat import DateFormat
import weasyprint

from core.domain.factura import Factura
from core.domain.socio import Socio

logger = logging.getLogger(__name__)

class DjangoPDFService:
    """
    Servicio de Infraestructura para generar PDFs (RIDEs).
    Patrón: Facade (Oculta la complejidad de WeasyPrint tras un método simple).
    """

    def generar_ride_factura(self, factura: Factura, socio: Socio, xml_clave_acceso: str) -> bytes:
        try:
            # LÓGICA DE NEGOCIO VISUAL
            # Extraemos el secuencial real desde la Clave de Acceso (posiciones 24 a 33) 
            # para garantizar que el PDF coincida SIEMPRE con lo enviado al SRI.
            # Nota: Clave acceso tiene 49 dígitos.
            # Posiciones estandar SRI:
            # Fecha (8) + T.Comp (2) + RUC (13) + Amb (1) + Estab (3) + PtoEmi (3) + Secuencial (9) + ...
            # 0-8: Fecha
            # 8-10: T.Comp
            # 10-23: RUC
            # 23: Ambiente
            # 24-27: Estab (3) -> Ojo: Python slice es [start:end]
            # 27-30: PtoEmi (3)
            # 30-39: Secuencial (9)
            
            # Verificamos longitud por seguridad
            if len(xml_clave_acceso) == 49:
                estab = xml_clave_acceso[24:27]
                pto = xml_clave_acceso[27:30]
                secuencial_real = xml_clave_acceso[30:39]
                numero_bonito = f"{estab}-{pto}-{secuencial_real}"
            else:
                # Fallback si por alguna razón la clave no tiene formato estándar
                numero_bonito = self._formatear_secuencial_fallback(factura.id)

            context = {
                # Usamos una imagen transparente o placeholder si no hay logo configurado
                # para evitar errores 404 en WeasyPrint
                'logo_url': self._get_logo_url(), 
                'emisor': {
                    'ruc': settings.SRI_EMISOR_RUC,
                    'razon_social': settings.SRI_EMISOR_RAZON_SOCIAL,
                    'direccion': settings.SRI_EMISOR_DIRECCION_MATRIZ,
                    'obligado': getattr(settings, 'SRI_OBLIGADO_CONTABILIDAD', 'NO'),
                    'ambiente': 'PRODUCCIÓN' if settings.SRI_AMBIENTE == 2 else 'PRUEBAS',
                },
                'factura': {
                    'numero_completo': numero_bonito, # DATO INMUTABLE
                    'clave_acceso': xml_clave_acceso,
                    'fecha_emision': DateFormat(factura.fecha_emision).format('d/m/Y'),
                    'fecha_autorizacion': DateFormat(factura.sri_fecha_autorizacion or factura.fecha_registro).format('d/m/Y H:i'),
                    'subtotal': factura.subtotal,
                    'total': factura.total,
                    # Pasamos el impuesto como variable por si cambia la ley
                    'label_iva': 'IVA 15%', 
                    'lectura': {
                        'valor': factura.lectura.valor if factura.lectura else 0,
                        'consumo': factura.lectura.consumo_del_mes if factura.lectura else 0
                    } if factura.lectura else None
                },
                'cliente': {
                    'nombre': f"{socio.nombres} {socio.apellidos}",
                    'identificacion': socio.identificacion,
                    'direccion': socio.direccion,
                    'email': socio.email or "No registrado",
                    'telefono': socio.telefono or "No registrado"
                },
                'detalles': factura.detalles
            }

            html_string = render_to_string('invoices/factura_ride.html', context)
            
            # Generación en Memoria
            pdf_file = BytesIO()
            weasyprint.HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf(target=pdf_file)
            
            return pdf_file.getvalue()

        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            # En Clean Architecture, las excepciones de infra no deben subir crudas
            raise ValueError(f"Error en el motor de reportes: {str(e)}")

    def _get_logo_url(self):
        """Intenta resolver la ruta local del logo para eficiencia"""
        import os
        # Prioridad: Static Root > App Static
        static_path = settings.STATIC_ROOT or os.path.join(settings.BASE_DIR, 'adapters', 'infrastructure', 'files', 'static')
        logo_path = os.path.join(static_path, 'img', 'logo.png')
        
        if os.path.exists(logo_path):
            return f"file://{logo_path}"
        return "" 
    
    def _formatear_secuencial_fallback(self, factura_id) -> str:
        estab = getattr(settings, 'SRI_SERIE_ESTABLECIMIENTO', '001')
        pto = getattr(settings, 'SRI_SERIE_PUNTO_EMISION', '001')
        secuencial = str(int(factura_id)).zfill(9)
        return f"{estab}-{pto}-{secuencial}"
