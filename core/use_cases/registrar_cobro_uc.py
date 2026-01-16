# core/use_cases/registrar_cobro_uc.py
from decimal import Decimal
from typing import List, Dict, Tuple
from django.db import transaction
from django.utils import timezone

# 1. Enums y Excepciones
from core.shared.enums import EstadoFactura, MetodoPagoEnum, RolUsuario
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

# 2. Modelos de Infraestructura (Base de Datos)
from adapters.infrastructure.models import FacturaModel, PagoModel

# 3. Servicios e Interfaces
from adapters.infrastructure.services.django_sri_service import DjangoSRIService

# 4. Entidades de Dominio
from core.domain.factura import Factura as FacturaEntity, DetalleFactura
from core.domain.socio import Socio as SocioEntity

class RegistrarCobroUseCase:
    """
    Gestiona la Recaudación y la Emisión Electrónica (SRI).
    Adapta los modelos de Django a tu Entidad de Dominio 'Socio' específica.
    """

    def __init__(self):
        self.sri_service = DjangoSRIService()

    def ejecutar(self, factura_id: int, lista_pagos: List[Dict]):
        with transaction.atomic():
            # A. Obtener Factura con relaciones necesarias
            try:
                factura_db = FacturaModel.objects.select_for_update()\
                    .select_related('socio', 'medidor')\
                    .prefetch_related('detalles')\
                    .get(id=factura_id)
            except FacturaModel.DoesNotExist:
                raise EntityNotFoundException(f"La factura {factura_id} no existe.")

            # B. Validaciones de Reglas de Negocio
            if factura_db.estado == EstadoFactura.PAGADA.value:
                raise BusinessRuleException("Esta factura ya se encuentra PAGADA.")
            
            if factura_db.estado == EstadoFactura.ANULADA.value:
                raise BusinessRuleException("No se puede cobrar una factura ANULADA.")

            # C. Procesamiento de Pagos
            total_pagado = Decimal("0.00")
            pagos_a_crear = []

            for p in lista_pagos:
                monto = Decimal(str(p['monto']))
                metodo = p['metodo']
                referencia = p.get('referencia')

                if metodo == MetodoPagoEnum.TRANSFERENCIA.value and not referencia:
                    raise BusinessRuleException("Pagos por transferencia requieren número de comprobante.")

                total_pagado += monto
                
                pagos_a_crear.append(PagoModel(
                    factura=factura_db,
                    metodo=metodo,
                    monto=monto,
                    referencia=referencia,
                    observacion=p.get('observacion')
                ))

            # D. Validación Cuadre de Caja
            if abs(factura_db.total - total_pagado) > Decimal("0.01"):
                raise BusinessRuleException(f"El monto recibido (${total_pagado}) no cubre el total de la factura (${factura_db.total}).")

            # E. Persistencia
            PagoModel.objects.bulk_create(pagos_a_crear)
            factura_db.estado = EstadoFactura.PAGADA.value
            factura_db.save()

            # ==========================================================
            # 🚀 FASE 2: ORQUESTACIÓN SRI
            # ==========================================================
            sri_resultado = {
                "enviado": False,
                "estado": "PENDIENTE_ENVIO",
                "mensaje": ""
            }

            try:
                # 1. Convertir Infraestructura -> Dominio (Aquí usamos tu Socio real)
                factura_entity, socio_entity = self._convertir_a_dominio(factura_db)

                # 2. Enviar al Servicio SRI
                respuesta_sri = self.sri_service.enviar_factura(factura_entity, socio_entity)
                
                # 3. Procesar Respuesta
                if respuesta_sri.exito:
                    factura_db.estado_sri = "AUTORIZADO"
                    factura_db.clave_acceso_sri = respuesta_sri.autorizacion_id
                    factura_db.xml_autorizado_sri = respuesta_sri.xml_respuesta
                    factura_db.fecha_autorizacion_sri = timezone.now()
                    
                    sri_resultado["enviado"] = True
                    sri_resultado["estado"] = "AUTORIZADO"
                else:
                    factura_db.estado_sri = respuesta_sri.estado
                    factura_db.mensaje_error_sri = respuesta_sri.mensaje_error
                    
                    sri_resultado["estado"] = respuesta_sri.estado
                    sri_resultado["mensaje"] = respuesta_sri.mensaje_error
                
                factura_db.save()

            except Exception as e:
                sri_resultado["estado"] = "ERROR_SISTEMA"
                sri_resultado["mensaje"] = str(e)
                # Aquí podrías agregar logs

            return {
                "mensaje": "Cobro registrado correctamente.",
                "factura_id": factura_db.id,
                "nuevo_estado": factura_db.estado,
                "sri": sri_resultado
            }

    def _convertir_a_dominio(self, f_db: FacturaModel) -> Tuple[FacturaEntity, SocioEntity]:
        """
        Mapper: Adapta el modelo DB a las Entidades de Dominio específicas.
        """
        
        # 1. Mapear Detalles
        detalles_dominio = []
        for det in f_db.detalles.all():
            detalles_dominio.append(DetalleFactura(
                id=det.id,
                concepto=det.concepto,
                cantidad=det.cantidad,
                precio_unitario=det.precio_unitario,
                subtotal=det.subtotal
            ))

        # 2. Mapear Socio (Adaptado a tu clase dataclass Socio)
        # Usamos valores seguros para SRI (evitar Nones en dirección/email si es posible)
        direccion_safe = f_db.socio.direccion if f_db.socio.direccion else "S/N"
        
        socio_dominio = SocioEntity(
            # Campos Obligatorios
            id=f_db.socio.id,
            cedula=f_db.socio.cedula,
            nombres=f_db.socio.nombres,
            apellidos=f_db.socio.apellidos,
            
            # Campos Opcionales (Mapeo directo)
            email=f_db.socio.email,
            telefono=f_db.socio.telefono,
            
            # Referencia ID
            barrio_id=f_db.socio.barrio_id, # Django expone el ID de la FK así
            direccion=direccion_safe,

            # Datos de Sistema
            rol=RolUsuario(f_db.socio.rol), # Convertimos string DB a Enum
            esta_activo=f_db.socio.esta_activo,
            usuario_id=f_db.socio.usuario_id, # Django expone el ID de la OneToOne así

            # Datos demográficos (No existen en BD aún, pasamos defaults del dataclass)
            fecha_nacimiento=None,
            discapacidad=False,
            tercera_edad=False
        )

        # 3. Mapear Factura
        factura_dominio = FacturaEntity(
            id=f_db.id,
            socio_id=f_db.socio.id,
            medidor_id=f_db.medidor.id if f_db.medidor else None,
            fecha_emision=f_db.fecha_emision,
            fecha_vencimiento=f_db.fecha_vencimiento,
            estado=EstadoFactura(f_db.estado),
            subtotal=f_db.subtotal,
            impuestos=f_db.impuestos,
            total=f_db.total,
            detalles=detalles_dominio,
            
            # Campos SRI
            sri_ambiente=f_db.sri_ambiente,
            sri_tipo_emision=f_db.sri_tipo_emision,
            sri_clave_acceso=f_db.clave_acceso_sri
        )

        return factura_dominio, socio_dominio