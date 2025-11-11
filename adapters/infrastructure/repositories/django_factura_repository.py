from typing import List, Optional
from datetime import date
from django.db import transaction

# Contratos (Interfaces) que vamos a implementar
from core.interfaces.repositories import IFacturaRepository
# Entidades (Clases puras) que el Caso de Uso espera recibir
from core.domain.factura import Factura, DetalleFactura
from core.domain.shared.enums import EstadoFactura
# Modelos (Clases de Django) que usaremos para la BBDD
from adapters.infrastructure.models import FacturaModel, DetalleFacturaModel, SocioModel, MedidorModel

class DjangoFacturaRepository(IFacturaRepository):
    """
    Implementación del Repositorio de Facturas usando el ORM de Django.
    Este es el "Adaptador" de la base de datos.
    """

    def _to_entity(self, model: FacturaModel) -> Factura:
        """Mapeador: Convierte un Modelo de Django a una Entidad de Dominio."""
        factura = Factura(
            id=model.id,
            socio_id=model.socio.id,
            medidor_id=model.medidor.id if model.medidor else None,
            fecha_emision=model.fecha_emision,
            fecha_vencimiento=model.fecha_vencimiento,
            estado=EstadoFactura(model.estado),
            subtotal=model.subtotal,
            impuestos=model.impuestos,
            total=model.total,
            # (lectura se maneja por separado si es necesario)
        )
        # Cargamos los detalles
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
        try:
            model = FacturaModel.objects.prefetch_related('detalles').get(pk=factura_id)
            return self._to_entity(model)
        except FacturaModel.DoesNotExist:
            return None
    
    @transaction.atomic # Asegura que la factura y sus detalles se guarden juntos
    def save(self, factura: Factura) -> Factura:
        """Guarda o actualiza una Factura y sus Detalles."""
        
        # 1. Preparar datos del modelo principal
        model_data = {
            'socio_id': factura.socio_id,
            'medidor_id': factura.medidor_id,
            'fecha_emision': factura.fecha_emision,
            'fecha_vencimiento': factura.fecha_vencimiento,
            'estado': factura.estado.value,
            'subtotal': factura.subtotal,
            'impuestos': factura.impuestos,
            'total': factura.total,
            'clave_acceso_sri': getattr(factura, 'clave_acceso_sri', None),
            'estado_sri': getattr(factura, 'estado_sri', None),
            'mensaje_sri': getattr(factura, 'mensaje_sri', None),
        }
        
        # 2. Crear o Actualizar
        if factura.id:
            FacturaModel.objects.filter(pk=factura.id).update(**model_data)
            factura_model = FacturaModel.objects.get(pk=factura.id)
            # Borramos detalles antiguos para re-crearlos
            factura_model.detalles.all().delete()
        else:
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

        return self._to_entity(factura_model) # Devuelve la entidad actualizada

    # ... (Implementarías list_by_socio_and_date_range y list_by_estado)
    def list_by_estado(self, estado: EstadoFactura) -> List[Factura]:
        models = FacturaModel.objects.filter(estado=estado.value)
        return [self._to_entity(m) for m in models]

    # ... otros métodos ...