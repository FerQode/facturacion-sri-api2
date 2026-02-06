# adapters/infrastructure/repositories/django_sri_repository.py
from django.db import transaction
from adapters.infrastructure.models.sri_models import SRISecuencialModel
from django.conf import settings

class DjangoSRISecuencialRepository:
    
    def obtener_siguiente_secuencial(self, tipo_comprobante='01') -> int:
        """
        Obtiene el siguiente número de factura de forma segura (Concurrency-safe).
        Usa 'select_for_update' para bloquear la fila durante la transacción.
        """
        # Obtenemos configuración default desde settings
        estab = settings.SRI_SERIE_ESTABLECIMIENTO
        pto_emi = settings.SRI_SERIE_PUNTO_EMISION
        
        with transaction.atomic():
            # Buscamos el contador para Facturas (01) del punto de emisión por defecto
            # select_for_update() es la CLAVE: Bloquea la fila en MySQL/Postgres
            secuencial, created = SRISecuencialModel.objects.select_for_update().get_or_create(
                codigo_establecimiento=estab,
                codigo_punto_emision=pto_emi,
                tipo_comprobante=tipo_comprobante,
                defaults={'secuencia_actual': 0} # Si no existe, empieza en 0
            )
            
            # Incrementamos
            nuevo_numero = secuencial.secuencia_actual + 1
            secuencial.secuencia_actual = nuevo_numero
            secuencial.save()
            
            return nuevo_numero
