# adapters/infrastructure/repositories/django_factura_repository.py

from typing import List, Optional
from datetime import date
from django.db import transaction

# El Contrato (Interfaz)
from core.interfaces.repositories import IFacturaRepository
# Las Entidades (Lógica Pura)
from core.domain.factura import Factura, DetalleFactura
# El Enum (Corregido)
from core.shared.enums import EstadoFactura
# Los Modelos (BBDD)
from adapters.infrastructure.models import FacturaModel, DetalleFacturaModel

class DjangoFacturaRepository(IFacturaRepository):
    """
    Implementación del Repositorio de Facturas usando el ORM de Django.
    """

    def _to_entity(self, model: FacturaModel) -> Factura:
        """Mapeador: Convierte un Modelo de Django a una Entidad de Dominio."""
        factura = Factura(
            id=model.id,
            socio_id=model.socio_id,
            medidor_id=model.medidor_id if model.medidor else None,
            lectura=None, # La lectura no se carga por defecto para evitar joins
            fecha_emision=model.fecha_emision,
            fecha_vencimiento=model.fecha_vencimiento,
            estado=EstadoFactura(model.estado),
            subtotal=model.subtotal,
            impuestos=model.impuestos,
            total=model.total,
        )
        
        # Cargamos los detalles (gracias al prefetch_related no gasta más BBDD)
        factura.detalles = [
            DetalleFactura(
                id=d.id,
                concepto=d.concepto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                subtotal=d.subtotal
            ) for d in model.detalles.all()
        ]
        
        # Cargamos datos del SRI
        factura.clave_acceso_sri = model.clave_acceso_sri
        factura.estado_sri = model.estado_sri
        factura.mensaje_sri = model.mensaje_sri
        
        return factura

    def get_by_id(self, factura_id: int) -> Optional[Factura]:
        """Busca una factura y sus detalles por ID."""
        try:
            # Buena Práctica: prefetch_related carga los 'detalles' en una
            # sola consulta SQL optimizada, en lugar de N+1 consultas.
            model = FacturaModel.objects.prefetch_related('detalles').get(pk=factura_id)
            return self._to_entity(model)
        except FacturaModel.DoesNotExist:
            return None
    
    # Buena Práctica: ¡Transacción Atómica!
    @transaction.atomic 
    def save(self, factura: Factura) -> Factura:
        """Guarda o actualiza una Factura y sus Detalles."""
        
        model_data = {
            'socio_id': factura.socio_id,
            'medidor_id': factura.medidor_id,
            'lectura_id': factura.lectura.id if factura.lectura else None,
            'fecha_emision': factura.fecha_emision,
            'fecha_vencimiento': factura.fecha_vencimiento,
            'estado': factura.estado.value, # Guardamos el valor (ej: "Pendiente")
            'subtotal': factura.subtotal,
            'impuestos': factura.impuestos,
            'total': factura.total,
            'clave_acceso_sri': getattr(factura, 'clave_acceso_sri', None),
            'estado_sri': getattr(factura, 'estado_sri', None),
            'mensaje_sri': getattr(factura, 'mensaje_sri', None),
            'xml_enviado_sri': getattr(factura, 'xml_enviado_sri', None),
            'xml_respuesta_sri': getattr(factura, 'xml_respuesta_sri', None)
        }
        
        if factura.id:
            # Actualiza
            FacturaModel.objects.filter(pk=factura.id).update(**model_data)
            factura_model = FacturaModel.objects.get(pk=factura.id)
            factura_model.detalles.all().delete() # Borramos detalles antiguos
        else:
            # Crea
            factura_model = FacturaModel.objects.create(**model_data)

        # 3. Crear los nuevos detalles
        detalles_a_crear = [
            DetalleFacturaModel(
                factura=factura_model,
                concepto=d.concepto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                subtotal=d.subtotal
            ) for d in factura.detalles
        ]
        DetalleFacturaModel.objects.bulk_create(detalles_a_crear)

        factura.id = factura_model.id
        return factura

    def list_by_socio_and_date_range(self, socio_id: int, fecha_inicio: date, fecha_fin: date) -> List[Factura]:
        """Busca facturas de un socio en un rango de fechas."""
        models = FacturaModel.objects.prefetch_related('detalles').filter(
            socio_id=socio_id, 
            fecha_emision__range=[fecha_inicio, fecha_fin]
        )
        return [self._to_entity(m) for m in models]

    def list_by_estado(self, estado: EstadoFactura) -> List[Factura]:
        """Busca facturas por estado (Pendiente, Pagada)."""
        models = FacturaModel.objects.prefetch_related('detalles').filter(estado=estado.value)
        return [self._to_entity(m) for m in models]