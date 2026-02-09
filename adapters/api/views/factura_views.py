# adapters/api/views/factura_views.py

from django.http import HttpResponse, Http404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiTypes

# Dominios y Servicios
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository
from adapters.infrastructure.services.pdf_service import DjangoPDFService
from adapters.infrastructure.models import FacturaModel

class DescargarRideView(APIView):
    """
    Endpoint para descargar el RIDE (PDF) de una factura.
    Ruta: GET /api/v1/facturas/{id}/pdf/
    """
    permission_classes = [IsAuthenticated] # Seguridad primero

    @extend_schema(
        summary="Descargar RIDE (PDF)",
        description="Genera y descarga el PDF (RIDE) de una factura autorizada por el SRI.",
        responses={
            200: OpenApiTypes.BINARY,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT
        }
    )
    def get(self, request, factura_id):
        try:
            # 1. Recuperar Entidades (Usando Repositorios, no ORM directo en la vista)
            # Nota: Para reportes visuales complejos como PDF, es aceptable leer del Modelo de Lectura (ORM)
            # si el Modelo de Dominio no tiene los campos de presentación necesarios.
            
            factura_orm = FacturaModel.objects.select_related('socio', 'lectura').get(id=factura_id)
            
            # VALIDACIÓN CRÍTICA:
            if not factura_orm.sri_clave_acceso:
                return Response(
                    {"error": "Esta factura aún no ha sido autorizada por el SRI. No tiene Clave de Acceso."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. Invocar Servicio PDF
            pdf_service = DjangoPDFService()
            
            # Truco: Django Templates leen objetos ORM igual que objetos de Dominio 
            # si tienen los mismos atributos.
            pdf_bytes = pdf_service.generar_ride_factura(
                factura=factura_orm, 
                socio=factura_orm.socio,
                xml_clave_acceso=factura_orm.sri_clave_acceso
            )

            # 3. Respuesta HTTP como Archivo
            filename = f"factura_{factura_orm.sri_clave_acceso}.pdf"
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            # 'attachment' descarga el archivo. 'inline' lo abre en el navegador.
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response

        except FacturaModel.DoesNotExist:
            raise Http404("Factura no encontrada")
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)