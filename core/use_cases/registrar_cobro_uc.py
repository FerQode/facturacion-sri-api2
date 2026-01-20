# core/use_cases/registrar_cobro_uc.py
from decimal import Decimal
from typing import List, Dict, Tuple
from django.db import transaction
from django.db.models import Sum  # ✅ IMPORTANTE: Para sumar pagos existentes
from django.utils import timezone
from django.conf import settings
# 1. Enums y Excepciones
from core.shared.enums import EstadoFactura, MetodoPagoEnum, RolUsuario
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

# 2. Modelos de Infraestructura (Base de Datos)
from adapters.infrastructure.models import FacturaModel, PagoModel

# 3. Servicios e Interfaces
from adapters.infrastructure.services.django_sri_service import DjangoSRIService
from adapters.infrastructure.services.django_email_service import DjangoEmailService

# 4. Entidades de Dominio
from core.domain.factura import Factura as FacturaEntity, DetalleFactura
from core.domain.socio import Socio as SocioEntity

class RegistrarCobroUseCase:
    """
    Gestiona la Recaudación, la Emisión Electrónica (SRI), Notificación y genera el Comprobante.
    Implementa el 'Candado de Seguridad' para validar transferencias previas.
    """

    def __init__(self):
        self.sri_service = DjangoSRIService()
        self.email_service = DjangoEmailService()

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

            # B. Validaciones de Estado
            if factura_db.estado == EstadoFactura.PAGADA.value:
                raise BusinessRuleException("Esta factura ya se encuentra PAGADA.")

            if factura_db.estado == EstadoFactura.ANULADA.value:
                raise BusinessRuleException("No se puede cobrar una factura ANULADA.")

            # ==================================================================
            # 🔒 C. LÓGICA DE CANDADO (TRANSFERENCIA VALIDADA + EFECTIVO)
            # ==================================================================

            # 1. Calcular Saldo ya cubierto por Transferencias VALIDADAS en BD
            suma_transferencias = PagoModel.objects.filter(
                factura=factura_db,
                metodo=MetodoPagoEnum.TRANSFERENCIA.value,
                validado=True
            ).aggregate(Sum('monto'))

            monto_transferencias_validas = suma_transferencias['monto__sum'] or Decimal("0.00")

            # 2. Verificar si existen Transferencias SIN VALIDAR (Bloqueo de Seguridad)
            hay_pendientes = PagoModel.objects.filter(
                factura=factura_db,
                metodo=MetodoPagoEnum.TRANSFERENCIA.value,
                validado=False
            ).exists()

            if hay_pendientes:
                raise BusinessRuleException("Error: Existen transferencias subidas pero NO verificadas por Tesorería. Vaya al módulo de validación primero.")

            # 3. Procesar los NUEVOS pagos que vienen del Cajero (Solo Efectivo)
            total_efectivo_entrante = Decimal("0.00")
            pagos_a_crear = []

            for p in lista_pagos:
                metodo = p['metodo']
                monto = Decimal(str(p['monto']))

                # 🛑 Ignoramos 'TRANSFERENCIA' si viene del frontend,
                # porque la transferencia ya debería estar en BD.
                if metodo == MetodoPagoEnum.TRANSFERENCIA.value:
                    continue

                total_efectivo_entrante += monto

                # El efectivo que ingresa en caja nace validado
                pagos_a_crear.append(PagoModel(
                    factura=factura_db,
                    metodo=metodo,
                    monto=monto,
                    referencia=p.get('referencia'),
                    observacion=p.get('observacion'),
                    validado=True
                ))

            # 4. CUADRE TOTAL
            total_acumulado = monto_transferencias_validas + total_efectivo_entrante

            # Verificamos si cubre el total (con margen de error de 1 centavo)
            faltante = factura_db.total - total_acumulado
            if faltante > Decimal("0.01"):
                raise BusinessRuleException(
                    f"Monto insuficiente. Faltan ${faltante}. "
                    f"(Transferencias Validadas: ${monto_transferencias_validas} + Efectivo Recibido: ${total_efectivo_entrante})"
                )

            # Validación opcional de sobrepago
            if total_acumulado > factura_db.total + Decimal("0.01"):
                 raise BusinessRuleException(f"El monto ingresado excede el total de la factura.")

            # ==================================================================
            # D. PERSISTENCIA Y CAMBIO DE ESTADO
            # ==================================================================

            # Guardamos solo los pagos nuevos (Efectivo)
            PagoModel.objects.filter(
                factura=factura_db,
                metodo=MetodoPagoEnum.EFECTIVO.value
            ).delete()

            # Guardamos solo los pagos nuevos (Efectivo)
            if pagos_a_crear:
                PagoModel.objects.bulk_create(pagos_a_crear)

            factura_db.estado = EstadoFactura.PAGADA.value
            factura_db.save()

            # ==========================================================
            # 🚀 FASE 2: ORQUESTACIÓN SRI (PERSISTENCIA PREVIA)
            # ==========================================================
            sri_resultado = {
                "enviado": False,
                "estado": "PENDIENTE_ENVIO",
                "mensaje": ""
            }

            try:
                # 1. GENERACIÓN PREVIA DE CLAVE (Sin internet)
                # Si la factura no tiene clave, la generamos y guardamos YA.
                if not factura_db.clave_acceso_sri:
                    numero_base = 1000 + int(factura_db.id)
                    nueva_clave = self.sri_service.generar_clave_acceso(
                        emisor_ruc=settings.SRI_EMISOR_RUC,
                        fecha_emision=factura_db.fecha_emision,
                        nro_factura=str(numero_base)
                    )
                    factura_db.clave_acceso_sri = nueva_clave
                    factura_db.estado_sri = "PENDIENTE_ENVIO"
                    factura_db.save(update_fields=['clave_acceso_sri', 'estado_sri'])

                # 2. Convertir a Dominio (Ahora la entidad ya lleva la clave)
                factura_entity, socio_entity = self._convertir_a_dominio(factura_db)

                # 3. INTENTO DE ENVÍO AL SRI
                respuesta_sri = self.sri_service.enviar_factura(factura_entity, socio_entity)

                # 4. Procesar Respuesta Final
                if respuesta_sri.exito:
                    factura_db.estado_sri = "AUTORIZADO"
                    factura_db.xml_autorizado_sri = respuesta_sri.xml_respuesta
                    factura_db.fecha_autorizacion_sri = timezone.now()

                    sri_resultado.update({"enviado": True, "estado": "AUTORIZADO", "mensaje": respuesta_sri.autorizacion_id})

                    # Notificación Email
                    self.email_service.enviar_notificacion_factura(
                        email_destinatario=factura_db.socio.email,
                        nombre_socio=f"{factura_db.socio.nombres} {factura_db.socio.apellidos}",
                        numero_factura=factura_db.id,
                        xml_autorizado=respuesta_sri.xml_respuesta
                    )
                else:
                    factura_db.estado_sri = respuesta_sri.estado
                    factura_db.mensaje_error_sri = respuesta_sri.mensaje_error
                    sri_resultado.update({"estado": respuesta_sri.estado, "mensaje": respuesta_sri.mensaje_error})

                factura_db.save()

            except Exception as e:
                # Si falla el internet, la clave YA ESTÁ GUARDADA en el paso 1.
                print(f"DEBUG: Error en envío SRI, pero la clave quedó a salvo: {e}")
                sri_resultado["estado"] = "PENDIENTE_ENVIO"
                sri_resultado["mensaje"] = "El documento se guardó localmente pero el SRI no respondió."

            # ==========================================================
            # ✅ FASE 3: CONSTRUIR EL COMPROBANTE FINAL
            # ==========================================================

            # Importante: Recuperamos TODOS los pagos (Transferencia vieja + Efectivo nuevo)
            # para que el recibo salga completo.
            todos_los_pagos = PagoModel.objects.filter(factura=factura_db)

            comprobante_data = {
                "factura": {
                    "id": factura_db.id,
                    "fecha_emision": factura_db.fecha_emision,
                    "subtotal": factura_db.subtotal,
                    "total": factura_db.total,
                    "estado_sri": factura_db.estado_sri,
                    "clave_acceso_sri": factura_db.clave_acceso_sri
                },
                "socio": {
                    "nombres": factura_db.socio.nombres,
                    "apellidos": factura_db.socio.apellidos,
                    "cedula": factura_db.socio.cedula,
                    "direccion": factura_db.socio.direccion
                },
                "pagos": [
                    {"metodo": p.metodo, "monto": p.monto} for p in todos_los_pagos
                ]
            }

            return {
                "mensaje": "Cobro registrado correctamente.",
                "factura_id": factura_db.id,
                "sri": sri_resultado,
                "comprobante": comprobante_data
            }

    def _convertir_a_dominio(self, f_db: FacturaModel) -> Tuple[FacturaEntity, SocioEntity]:
        detalles_dominio = []
        for det in f_db.detalles.all():
            detalles_dominio.append(DetalleFactura(
                id=det.id, concepto=det.concepto, cantidad=det.cantidad,
                precio_unitario=det.precio_unitario, subtotal=det.subtotal
            ))

        direccion_safe = f_db.socio.direccion if f_db.socio.direccion else "S/N"

        socio_dominio = SocioEntity(
            id=f_db.socio.id, cedula=f_db.socio.cedula, nombres=f_db.socio.nombres,
            apellidos=f_db.socio.apellidos, email=f_db.socio.email, telefono=f_db.socio.telefono,
            barrio_id=f_db.socio.barrio_id, direccion=direccion_safe,
            rol=RolUsuario(f_db.socio.rol), esta_activo=f_db.socio.esta_activo,
            usuario_id=f_db.socio.usuario_id, fecha_nacimiento=None, discapacidad=False, tercera_edad=False
        )

        factura_dominio = FacturaEntity(
            id=f_db.id, socio_id=f_db.socio.id, medidor_id=f_db.medidor.id if f_db.medidor else None,
            fecha_emision=f_db.fecha_emision, fecha_vencimiento=f_db.fecha_vencimiento,
            estado=EstadoFactura(f_db.estado), subtotal=f_db.subtotal, impuestos=f_db.impuestos,
            total=f_db.total, detalles=detalles_dominio, sri_ambiente=f_db.sri_ambiente,
            sri_tipo_emision=f_db.sri_tipo_emision, sri_clave_acceso=f_db.clave_acceso_sri
        )
        return factura_dominio, socio_dominio