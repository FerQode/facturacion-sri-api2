# adapters/api/views/sri_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

# Use Cases
from core.use_cases.sincronizar_sri_uc import SincronizarFacturaSRIUseCase

# Repositories (Infrastructure)
from adapters.infrastructure.repositories.django_factura_repository import DjangoFacturaRepository

# Services (Infrastructure)
from adapters.infrastructure.services.django_sri_service import DjangoSRIService
from adapters.infrastructure.services.django_email_service import DjangoEmailService # Asumimos que existe por contexto

class SRIViewSet(viewsets.ViewSet):
    """
    ViewSet para acciones directas relacionadas con el SRI.
    Separado de Cobros y Facturas para mantener SRP.
    """

    @action(detail=True, methods=['post'], url_path='sincronizar')
    def sincronizar(self, request, pk=None):
        """
        POST /api/v1/sri/{pk}/sincronizar/
        Reintenta o consulta el estado de una factura en el SRI.
        Útil para errores 'CLAVE DE ACCESO EN PROCESAMIENTO' o 'DEVUELTA'.
        """
        try:
            # Composición de Dependencias (Manual DI)
            # En un proyecto más grande usaríamos un Container (Dependency Injector)
            factura_repo = DjangoFacturaRepository()
            sri_service = DjangoSRIService() 
            email_service = DjangoEmailService() # Instancia por defecto

            use_case = SincronizarFacturaSRIUseCase(
                factura_repo=factura_repo,
                sri_service=sri_service,
                email_service=email_service
            )

            resultado = use_case.ejecutar(factura_id=int(pk))
            
            return Response(resultado, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
