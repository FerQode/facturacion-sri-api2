from datetime import date
from typing import List, Optional
from django.db import transaction

# El Contrato (Interfaz)
from core.interfaces.repositories import IFacturaRepository
# Las Entidades (Lógica Pura)
from core.domain.factura import Factura, DetalleFactura
# El Enum
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
            lectura=None, 
            fecha_emision=model.fecha_emision,
            fecha_vencimiento=model.fecha_vencimiento,
            
            # --- CORRECCIÓN IMPORTANTE ---
            # Recuperamos la fecha real de creación desde la BBDD.
            # Al tener USE_TZ=True, Django nos devuelve esto con la zona horaria correcta.
            fecha_registro=model.fecha_registro,
            # -----------------------------

            estado=EstadoFactura(model.estado),
            subtotal=model.subtotal,
            impuestos=model.impuestos,
            total=model.total,
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
        
        # --- Mapeo de campos SRI ---
        factura.sri_clave_acceso = model.clave_acceso_sri
        factura.estado_sri = model.estado_sri
        factura.sri_mensaje_error = model.mensaje_error_sri 
        factura.sri_xml_autorizado = model.xml_autorizado_sri
        factura.sri_fecha_autorizacion = model.fecha_autorizacion_sri
        
        return factura

    def get_by_id(self, factura_id: int) -> Optional[Factura]:
        try:
            model = FacturaModel.objects.prefetch_related('detalles').get(pk=factura_id)
            return self._to_entity(model)
        except FacturaModel.DoesNotExist:
            return None
    
    @transaction.atomic 
    def save(self, factura: Factura) -> Factura:
        model_data = {
            'socio_id': factura.socio_id,
            'medidor_id': factura.medidor_id,
            'lectura_id': factura.lectura.id if factura.lectura else None,
            
            # Aquí se guarda la fecha 'Aware' (con zona horaria) que viene de la Entidad
            'fecha_registro': factura.fecha_registro, 

            'fecha_emision': factura.fecha_emision,
            'fecha_vencimiento': factura.fecha_vencimiento,
            'estado': factura.estado.value if hasattr(factura.estado, 'value') else factura.estado,
            'subtotal': factura.subtotal,
            'impuestos': factura.impuestos,
            'total': factura.total,
            
            'clave_acceso_sri': getattr(factura, 'sri_clave_acceso', None),
            'estado_sri': getattr(factura, 'estado_sri', None),
            'mensaje_error_sri': getattr(factura, 'sri_mensaje_error', None),
            'xml_autorizado_sri': getattr(factura, 'sri_xml_autorizado', None),
            'fecha_autorizacion_sri': getattr(factura, 'sri_fecha_autorizacion', None),
        }
        
        if factura.id:
            # Actualiza
            FacturaModel.objects.filter(pk=factura.id).update(**model_data)
            factura_model = FacturaModel.objects.get(pk=factura.id)
            factura_model.detalles.all().delete() 
        else:
            # Crea
            factura_model = FacturaModel.objects.create(**model_data)

        # Crear los nuevos detalles
        if factura.detalles:
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

    def list_by_socio(self, socio_id: int) -> List[Factura]:
        models = FacturaModel.objects.prefetch_related('detalles').filter(socio_id=socio_id)
        return [self._to_entity(m) for m in models]

    def list_by_socio_and_date_range(self, socio_id: int, fecha_inicio: date, fecha_fin: date) -> List[Factura]:
        models = FacturaModel.objects.prefetch_related('detalles').filter(
            socio_id=socio_id, 
            fecha_emision__range=[fecha_inicio, fecha_fin]
        )
        return [self._to_entity(m) for m in models]

    def list_by_estado(self, estado: EstadoFactura) -> List[Factura]:
        models = FacturaModel.objects.prefetch_related('detalles').filter(estado=estado.value)
        return [self._to_entity(m) for m in models]
    
    def get_by_clave_acceso(self, clave_acceso: str) -> Optional[Factura]:
        try:
            model = FacturaModel.objects.prefetch_related('detalles').get(clave_acceso_sri=clave_acceso)
            return self._to_entity(model)
        except FacturaModel.DoesNotExist:
            return None
        
    def get_by_lectura_id(self, lectura_id: int) -> Optional[Factura]:
        try:
            model = FacturaModel.objects.prefetch_related('detalles').get(lectura_id=lectura_id)
            return self._to_entity(model)
        except FacturaModel.DoesNotExist:
            return None