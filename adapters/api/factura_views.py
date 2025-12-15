# adapters/api/views/factura_views.py

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# ... (tus otras importaciones y vistas existentes) ...

class MisFacturasAPIView(APIView):
    """
    Vista para que un Socio autenticado vea solo SUS propias facturas.
    """
    permission_classes = [IsAuthenticated] # Solo usuarios logueados

    def get(self, request):
        # 1. Obtener el usuario logueado
        usuario = request.user
        
        # TODO: Aquí implementaremos la lógica para buscar al Socio
        # asociado a este usuario y luego buscar sus facturas.
        
        return Response({
            "mensaje": "Aquí se mostrarán las facturas del usuario: " + usuario.username
        }, status=status.HTTP_200_OK)