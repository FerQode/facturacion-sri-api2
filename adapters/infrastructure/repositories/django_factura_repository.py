from datetime import date
from typing import List, Optional
from django.db import transaction

# Interfaces y Dominio
from core.interfaces.repositories import IFacturaRepository
from core.domain.factura import Factura, DetalleFactura
from core.shared.enums import EstadoFactura

# Modelos (Infraestructura)
from adapters.infrastructure.models import FacturaModel, DetalleFacturaModel

class DjangoFacturaRepository(IFacturaRepository):
    """
    Implementación completa del Repositorio de Facturas.
    Cumple estrictamente con IFacturaRepository.
    """

    # =================================================================
    # 1. MAPPER (Traductor: DB -> Dominio)
    # =================================================================
    def _map_model_to_domain(self, model: FacturaModel) -> Factura:
        """
        Convierte un Modelo Django (BD) a una Entidad de Negocio (Dominio).
        Protege contra errores de formato en Enums.
        """
        # 🛡️ Protección robusta para el Enum de Estado
        try:
            # Intento 1: Conversión directa (ej: "PENDIENTE")
            estado_enum = EstadoFactura(model.estado)
        except (ValueError, TypeError):
            try:
                # Intento 2: Normalización (ej: "Pendiente" -> "PENDIENTE")
                estado_enum = EstadoFactura(model.estado.upper())
            except (ValueError, AttributeError):
                # Fallback: Si el dato está corrupto, asumimos PENDIENTE por seguridad
                estado_enum = EstadoFactura.PENDIENTE

        # Construcción de la Entidad
        factura = Factura(
            id=model.id,
            socio_id=model.socio_id,
            medidor_id=model.medidor_id,
            # No cargamos la entidad completa para evitar circularidad
            lectura=None, 
            
            fecha_emision=model.fecha_emision,
            fecha_vencimiento=model.fecha_vencimiento,
            
            # Django maneja Timezones (Aware), lo pasamos directo
            fecha_registro=model.fecha_registro,
            
            estado=estado_enum,
            
            # Convertimos Decimal a float si el dominio lo requiere
            subtotal=float(model.subtotal),
            impuestos=float(model.impuestos),
            total=float(model.total),
            
            # Campos SRI
            sri_clave_acceso=model.clave_acceso_sri,
            estado_sri=model.estado_sri,
            sri_mensaje_error=model.mensaje_error_sri 
        )

        # Mapeo de Detalles (Nested Objects)
        detalles_qs = getattr(model, 'detalles', None)
        if detalles_qs:
            factura.detalles = [
                DetalleFactura(
                    id=d.id,
                    concepto=d.concepto,
                    cantidad=float(d.cantidad),
                    precio_unitario=float(d.precio_unitario),
                    subtotal=float(d.subtotal)
                ) for d in detalles_qs.all()
            ]

        return factura

    # =================================================================
    # 2. IMPLEMENTACIÓN DE INTERFAZ (Lectura)
    # =================================================================
    def get_by_id(self, factura_id: int) -> Optional[Factura]:
        try:
            # prefetch_related es CRÍTICO para rendimiento (evita N+1 queries)
            model = FacturaModel.objects.prefetch_related('detalles').get(pk=factura_id)
            return self._map_model_to_domain(model)
        except FacturaModel.DoesNotExist:
            return None

    def get_by_clave_acceso(self, clave_acceso: str) -> Optional[Factura]:
        try:
            model = FacturaModel.objects.prefetch_related('detalles').get(clave_acceso_sri=clave_acceso)
            return self._map_model_to_domain(model)
        except FacturaModel.DoesNotExist:
            return None

    # ✅ IMPLEMENTADO: Método requerido por la interfaz
    def get_by_lectura_id(self, lectura_id: int) -> Optional[Factura]:
        """Busca si ya existe una factura asociada a una lectura."""
        try:
            model = FacturaModel.objects.prefetch_related('detalles').get(lectura_id=lectura_id)
            return self._map_model_to_domain(model)
        except FacturaModel.DoesNotExist:
            return None

    def list_by_socio(self, socio_id: int) -> List[Factura]:
        models = FacturaModel.objects.prefetch_related('detalles').filter(socio_id=socio_id).order_by('-fecha_emision')
        return [self._map_model_to_domain(m) for m in models]

    # ✅ IMPLEMENTADO: Método requerido por la interfaz
    def list_by_socio_and_date_range(self, socio_id: int, fecha_inicio: date, fecha_fin: date) -> List[Factura]:
        """Lista facturas de un socio en un rango de fechas de emisión."""
        models = FacturaModel.objects.prefetch_related('detalles').filter(
            socio_id=socio_id,
            fecha_emision__range=[fecha_inicio, fecha_fin]
        ).order_by('-fecha_emision')
        return [self._map_model_to_domain(m) for m in models]

    # ✅ IMPLEMENTADO: Método requerido por la interfaz
    def list_by_estado(self, estado: EstadoFactura) -> List[Factura]:
        """Lista todas las facturas que coinciden con un estado específico."""
        # Manejo seguro por si pasan el Enum o el string value
        val = estado.value if hasattr(estado, 'value') else str(estado)
        
        models = FacturaModel.objects.prefetch_related('detalles').filter(
            estado__iexact=val
        ).order_by('-fecha_emision')
        return [self._map_model_to_domain(m) for m in models]

    def obtener_pendientes_por_socio(self, socio_id: int) -> List[Factura]:
        """
        Método especializado para la consulta de deuda.
        Usa 'iexact' para ignorar mayúsculas/minúsculas en la búsqueda.
        """
        models = FacturaModel.objects.prefetch_related('detalles').filter(
            socio_id=socio_id,
            estado__iexact=EstadoFactura.PENDIENTE.value
        ).order_by('fecha_emision')
        return [self._map_model_to_domain(m) for m in models]

    # =================================================================
    # 3. IMPLEMENTACIÓN DE INTERFAZ (Escritura)
    # =================================================================
    @transaction.atomic 
    def save(self, factura: Factura) -> Factura:
        """
        Guarda o actualiza una factura y sus detalles de forma atómica.
        """
        # Preparar diccionario de datos plano
        model_data = {
            'socio_id': factura.socio_id,
            'medidor_id': factura.medidor_id,
            'lectura_id': factura.lectura.id if factura.lectura else None,
            
            # Fechas
            'fecha_emision': factura.fecha_emision,
            'fecha_vencimiento': factura.fecha_vencimiento,
            
            # Estado y Montos
            'estado': factura.estado.value if hasattr(factura.estado, 'value') else factura.estado,
            'subtotal': factura.subtotal,
            'impuestos': factura.impuestos,
            'total': factura.total,
            
            # SRI
            'clave_acceso_sri': getattr(factura, 'sri_clave_acceso', None),
            'estado_sri': getattr(factura, 'estado_sri', None),
            'mensaje_error_sri': getattr(factura, 'sri_mensaje_error', None),
            'xml_autorizado_sri': getattr(factura, 'sri_xml_autorizado', None),
            'fecha_autorizacion_sri': getattr(factura, 'sri_fecha_autorizacion', None),
        }
        
        # Si la entidad tiene fecha_registro, la respetamos
        if factura.fecha_registro:
            model_data['fecha_registro'] = factura.fecha_registro

        # 1. Guardar Cabecera (Update or Create)
        if factura.id:
            FacturaModel.objects.filter(pk=factura.id).update(**model_data)
            factura_model = FacturaModel.objects.get(pk=factura.id)
            
            # Estrategia de reemplazo completo de detalles
            if factura.detalles is not None:
                factura_model.detalles.all().delete()
        else:
            factura_model = FacturaModel.objects.create(**model_data)

        # 2. Guardar Detalles (Bulk Create para rendimiento)
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

        # Actualizamos el ID de la entidad y retornamos mapeado
        factura.id = factura_model.id
        # Recargamos con prefetch para asegurar que los detalles vienen en el retorno
        factura_model_completa = FacturaModel.objects.prefetch_related('detalles').get(pk=factura_model.id)
        
        return self._map_model_to_domain(factura_model_completa)