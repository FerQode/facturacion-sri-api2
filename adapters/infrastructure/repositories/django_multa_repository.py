from typing import List, Dict
from adapters.infrastructure.models.multa_model import MultaModel

class DjangoMultaRepository:
    """
    Repositorio para acceder a la tabla de Multas usando el ORM.
    """
    
    def obtener_pendientes_por_socio(self, socio_id: int) -> List[Dict]:
        """
        Devuelve una lista simple de multas no pagadas.
        """
        qs = MultaModel.objects.filter(socio_id=socio_id, estado='PENDIENTE')
        
        # Retornamos diccionarios para facilitar el consumo en el servicio
        return [
            {
                'id': m.id, 
                'motivo': m.motivo, 
                'valor': m.valor
            } 
            for m in qs
        ]