from typing import Optional
from core.interfaces.repositories import IFacturaRepository
from core.domain.factura import Factura as FacturaEntity, DetalleFactura, EstadoFactura
from core.domain.socio import Socio as SocioEntity, RolUsuario
from adapters.infrastructure.models import FacturaModel

class DjangoFacturaRepository(IFacturaRepository):
    
    def obtener_por_id(self, id: int) -> Optional[FacturaEntity]:
        try:
            # Obtenemos el modelo de ORM con relaciones optimizadas
            f_db = FacturaModel.objects.select_related('socio', 'medidor').prefetch_related('detalles').get(id=id)
            
            # Mapeamos a Entidad de Dominio
            factura_entity = self._mapear_a_dominio(f_db)
            
            # Enriquecemos con el objeto Socio (Pragmatismo para no romper dataclass original por ahora)
            # Esto permite que el caso de uso acceda a datos del socio sin hacer queries
            socio_entity = self._mapear_socio(f_db.socio)
            setattr(factura_entity, 'socio_obj', socio_entity)
            
            return factura_entity
        
        except FacturaModel.DoesNotExist:
            return None

    def get_by_lectura_id(self, lectura_id: int) -> Optional[FacturaEntity]:
        try:
            f_db = FacturaModel.objects.filter(lectura_id=lectura_id).first()
            if f_db:
                return self._mapear_a_dominio(f_db)
            return None
        except Exception:
            return None

    def existe_factura_fija_mes(self, servicio_id: int, anio: int, mes: int) -> bool:
        return FacturaModel.objects.filter(
            servicio_id=servicio_id,
            anio=anio,
            mes=mes,
            estado__in=[EstadoFactura.PENDIENTE.value, EstadoFactura.PAGADA.value]
        ).exists()

    def guardar(self, factura: FacturaEntity) -> None:
        # Aquí actualizamos el registro en BD desde la Entidad
        # Asumimos que la entidad tiene ID (es update)
        if not factura.id:
            # Creación de nueva factura
            f_db = FacturaModel.objects.create(
                socio_id=factura.socio_id,
                servicio_id=factura.servicio_id,
                medidor_id=factura.medidor_id,
                lectura_id=factura.lectura.id if factura.lectura else None,
                fecha_emision=factura.fecha_emision,
                fecha_vencimiento=factura.fecha_vencimiento,
                anio=factura.anio,
                mes=factura.mes,
                estado=factura.estado.value if hasattr(factura.estado, 'value') else factura.estado,
                subtotal=factura.subtotal,
                impuestos=factura.impuestos,
                total=factura.total,
                sri_ambiente=factura.sri_ambiente,
                sri_tipo_emision=factura.sri_tipo_emision
            )
            factura.id = f_db.id # Actualizamos ID en dominio
            
            from adapters.infrastructure.models import DetalleFacturaModel

            for det in factura.detalles:
                DetalleFacturaModel.objects.create(
                    factura=f_db,
                    concepto=det.concepto,
                    cantidad=det.cantidad,
                    precio_unitario=det.precio_unitario,
                    subtotal=det.subtotal
                )
            
            return

        try:
            f_db = FacturaModel.objects.get(id=factura.id)
            
            # Actualizamos campos modificables por el Caso de Uso Concepto
            f_db.estado = factura.estado.value if hasattr(factura.estado, 'value') else factura.estado
            f_db.anio = factura.anio
            f_db.mes = factura.mes
            
            # Asociaciones (Lectura, Servicio)
            if factura.servicio_id:
                f_db.servicio_id = factura.servicio_id
            
            # Campos SRI
            f_db.sri_ambiente = factura.sri_ambiente
            f_db.sri_tipo_emision = factura.sri_tipo_emision
            f_db.clave_acceso_sri = factura.sri_clave_acceso
            f_db.xml_autorizado_sri = factura.sri_xml_autorizado
            f_db.mensaje_error_sri = factura.sri_mensaje_error
            f_db.estado_sri = factura.estado_sri
            if factura.sri_fecha_autorizacion:
                f_db.fecha_autorizacion_sri = factura.sri_fecha_autorizacion

            f_db.save()
            
        except FacturaModel.DoesNotExist:
            raise ValueError(f"Factura {factura.id} no encontrada en DB para guardar.")

    def _mapear_a_dominio(self, f_db: FacturaModel) -> FacturaEntity:
        detalles_dominio = []
        for det in f_db.detalles.all():
            detalles_dominio.append(DetalleFactura(
                id=det.id, concepto=det.concepto, cantidad=det.cantidad,
                precio_unitario=det.precio_unitario, subtotal=det.subtotal
            ))

        return FacturaEntity(
            id=f_db.id,
            socio_id=f_db.socio.id,
            servicio_id=f_db.servicio.id if f_db.servicio else None,
            medidor_id=f_db.medidor.id if f_db.medidor else None,
            fecha_emision=f_db.fecha_emision,
            fecha_vencimiento=f_db.fecha_vencimiento,
            anio=f_db.anio,
            mes=f_db.mes,
            estado=EstadoFactura(f_db.estado),
            subtotal=f_db.subtotal,
            impuestos=f_db.impuestos,
            total=f_db.total,
            detalles=detalles_dominio,
            sri_ambiente=f_db.sri_ambiente,
            sri_tipo_emision=f_db.sri_tipo_emision,
            sri_clave_acceso=f_db.clave_acceso_sri,
            sri_xml_autorizado=f_db.xml_autorizado_sri,
            sri_mensaje_error=f_db.mensaje_error_sri,
            estado_sri=f_db.estado_sri,
            # Mapeo de archivos
            archivo_pdf=f_db.archivo_pdf.url if f_db.archivo_pdf else None,
            archivo_xml_path=f_db.archivo_xml.url if f_db.archivo_xml else None
        )

    def obtener_pendientes_por_socio(self, socio_id: int) -> list[FacturaEntity]:
        f_dbs = FacturaModel.objects.filter(
            socio_id=socio_id,
            estado=EstadoFactura.PENDIENTE.value
        ).select_related('socio', 'medidor', 'servicio').prefetch_related('detalles')
        
        return [self._mapear_a_dominio(f) for f in f_dbs]

    def _mapear_socio(self, socio_db) -> SocioEntity:
        # Mapper auxiliar para el socio
        direccion_safe = socio_db.direccion if socio_db.direccion else "S/N"
        return SocioEntity(
            id=socio_db.id,
            cedula=socio_db.cedula,
            nombres=socio_db.nombres,
            apellidos=socio_db.apellidos,
            email=socio_db.email,
            telefono=socio_db.telefono,
            barrio_id=socio_db.barrio_id,
            direccion=direccion_safe,
            rol=RolUsuario(socio_db.rol),
            esta_activo=socio_db.esta_activo,
            usuario_id=socio_db.usuario_id,
            # Defaults
            fecha_nacimiento=None,
            discapacidad=False,
            tercera_edad=False
        )