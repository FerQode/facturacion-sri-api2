# adapters/api/views/factura_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# NOTA: Aquí importaremos tus Casos de Uso de Facturación cuando los creemos en el Core.
# from core.use_cases.facturacion.generar_factura_uc import GenerarFacturaUseCase
# from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository

# =============================================================================
# 1. GENERAR FACTURA (Cálculo + XML + Firma)
# =============================================================================
class GenerarFacturaAPIView(APIView):
    """
    Vista para generar la factura electrónica.
    Toma las lecturas, calcula consumo, genera XML y lo firma.
    """
    # permission_classes = [IsAdminUser] # Restringir a Tesoreros/Admins

    @swagger_auto_schema(
        operation_description="Genera, firma y guarda una factura basada en una lectura.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'lectura_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la lectura a facturar"),
            },
            required=['lectura_id']
        ),
        responses={200: "Factura Generada", 400: "Error de validación"}
    )
    def post(self, request):
        # TODO: Implementar lógica con GenerarFacturaUseCase
        lectura_id = request.data.get('lectura_id')
        
        return Response({
            "mensaje": f"Proceso iniciado: Generando factura para lectura {lectura_id}",
            "estado": "PENDIENTE_IMPLEMENTACION",
            "nota": "Aquí se invocará al Core para crear el XML firmado."
        }, status=status.HTTP_200_OK)


# =============================================================================
# 2. ENVIAR AL SRI (Consumo de Web Service)
# =============================================================================
class EnviarFacturaSRIAPIView(APIView):
    """
    Vista para enviar una factura YA firmada al SRI (Ambiente Pruebas/Producción).
    """
    @swagger_auto_schema(
        operation_description="Envía el XML firmado al Web Service del SRI.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'factura_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['factura_id']
        ),
        responses={200: "Recibido por SRI", 500: "Rechazado por SRI"}
    )
    def post(self, request):
        factura_id = request.data.get('factura_id')
        
        return Response({
            "mensaje": "Conectando con SRI...",
            "factura_id": factura_id,
            "estado_sri": "RECIBIDA (Simulado)"
        }, status=status.HTTP_200_OK)


# =============================================================================
# 3. CONSULTAR AUTORIZACIÓN (Estado SRI)
# =============================================================================
class ConsultarAutorizacionAPIView(APIView):
    """
    Vista para preguntar al SRI si la factura fue AUTORIZADA.
    """
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('clave_acceso', openapi.IN_QUERY, description="Clave de acceso de 49 dígitos", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request):
        clave = request.query_params.get('clave_acceso')
        
        return Response({
            "clave_acceso": clave,
            "estado": "AUTORIZADO",
            "mensaje": "El SRI ha validado el comprobante (Simulado)"
        }, status=status.HTTP_200_OK)


# =============================================================================
# 4. MIS FACTURAS (Portal del Socio)
# =============================================================================
class MisFacturasAPIView(APIView):
    """
    Vista para que un Socio autenticado vea SU historial de consumo y cobros.
    """
    permission_classes = [IsAuthenticated] # Solo usuarios logueados

    @swagger_auto_schema(
        operation_description="Obtiene las facturas del socio logueado actualmente.",
        responses={200: "Lista de facturas"}
    )
    def get(self, request):
        # 1. Obtener el usuario logueado (viene del Token JWT)
        usuario = request.user
        
        try:
            # 2. Intentar obtener el perfil de socio asociado
            # Recordar: En SocioModel definimos related_name='perfil_socio'
            socio = usuario.perfil_socio 
            
            # TODO: Conectar con FacturaRepository
            # facturas = DjangoFacturaRepository().get_by_socio_id(socio.id)
            # data = FacturaSerializer(facturas, many=True).data
            
            # Mock de respuesta por ahora
            return Response({
                "usuario": usuario.username,
                "socio_id": socio.id,
                "nombre_socio": f"{socio.nombres} {socio.apellidos}",
                "facturas": [
                    {"mes": "Enero", "consumo": "20m3", "total": 5.50, "estado": "PAGADO"},
                    {"mes": "Febrero", "consumo": "22m3", "total": 6.05, "estado": "PENDIENTE"}
                ]
            }, status=status.HTTP_200_OK)

        except AttributeError:
            # Si el usuario es admin/staff pero no tiene un perfil de Socio creado
            return Response({
                "error": "El usuario actual no tiene un perfil de Socio asociado."
            }, status=status.HTTP_404_NOT_FOUND)