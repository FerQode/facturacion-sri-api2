# core/use_cases/pos/facturar_venta_directa.py
from datetime import date
from decimal import Decimal
from typing import List, TypedDict
from django.db import transaction
from django.utils import timezone

from adapters.infrastructure.models import (
    ProductoMaterial, FacturaModel, DetalleFacturaModel, 
    PagoModel, DetallePagoModel, SocioModel, CatalogoRubroModel
)
from adapters.infrastructure.services.django_sri_service import DjangoSRIService
from core.shared.enums import MetodoPagoEnum

class ItemVenta(TypedDict):
    producto_id: int
    cantidad: int

class FacturarVentaDirectaUseCase:
    """
    Motor Transaccional para Punto de Venta (POS).
    Realiza Venta, Descuento de Stock, Facturación y Pago en una sola transacción ACID.
    """

    def __init__(self):
        self.sri_service = DjangoSRIService()

    @transaction.atomic
    def ejecutar(self, cliente_id: int, items: List[ItemVenta], forma_pago: str, usuario_id: int = None) -> dict:
        # 1. Validar Cliente (Socio o Consumidor Final)
        try:
            cliente = SocioModel.objects.get(id=cliente_id)
        except SocioModel.DoesNotExist:
            raise ValueError("Cliente no encontrado.")

        # 2. Inicializar Factura
        factura = FacturaModel.objects.create(
            socio=cliente,
            fecha_emision=date.today(),
            fecha_vencimiento=date.today(), # Venta contado
            subtotal=Decimal('0.00'),
            total=Decimal('0.00'),
            estado='PAGADA', # Nace pagada
            es_fiscal=True 
            # usuario_creacion_id=usuario_id
        )

        total_venta = Decimal('0.00')
        items_procesados = []

        # 3. Procesar Items (Con Bloqueo de Stock)
        for item in items:
            prod_id = item['producto_id']
            qty = item['cantidad']

            # SELECT FOR UPDATE: Bloqueo pesimista para evitar sobreventas
            producto = ProductoMaterial.objects.select_for_update().get(id=prod_id)

            if producto.stock_actual < qty:
                raise ValueError(f"Stock insuficiente para '{producto.nombre}'. Solo quedan {producto.stock_actual} unidades.")

            # Descontar Stock
            producto.stock_actual -= qty
            producto.save()

            # Calcular Valores
            valor_unitario = producto.precio_unitario
            subtotal_linea = valor_unitario * qty
            
            # IVA
            valor_iva_linea = Decimal('0.00')
            if producto.graba_iva:
                valor_iva_linea = subtotal_linea * Decimal('0.15') # IVA 15% Hardcoded por ahora (paramatrizar idealmente)
            
            total_linea = subtotal_linea + valor_iva_linea
            total_venta += total_linea

            # Crear Detalle Factura
            # Nota: DetalleFacturaModel suele tener FK a Lectura (agua) o Rubro. 
            # Adaptamos para apuntar al Rubro del Material.
            DetalleFacturaModel.objects.create(
                factura=factura,
                rubro=producto.rubro, # Usamos el rubro contable del producto
                cantidad=qty,
                precio_unitario=valor_unitario, # Explicitly matching model field
                subtotal=total_linea, # DetalleFactura suele guardar el total con/sin iva? Revisar modelo.
                # Asumimos que guarda el valor final de la linea o subtotal base.
                # Ajuste: Guardamos descripción del producto en campo auxiliar si existe o en el rubro dinámico
                concepto=f"{producto.nombre} (x{qty})" 
            )
            
            items_procesados.append({
                "producto": producto.nombre,
                "cantidad": qty,
                "total": total_linea
            })

        # 4. Actualizar Totales Factura
        factura.total = total_venta
        # factura.subtotal ... (si existe campo, calcular sumando bases)
        factura.save()

        # 5. Generar Pago Automático (Contado)
        pago = PagoModel.objects.create(
            socio=cliente,
            monto_total=total_venta,
            fecha_registro=timezone.now(),
            observacion=f"Venta Directa POS. Factura #{factura.id}"
        )
        
        DetallePagoModel.objects.create(
            pago=pago,
            metodo=forma_pago,
            monto=total_venta
        )

        sri_response = None
        estado_sri_final = "PENDIENTE"
        clave_acceso_final = None

        try:
            # 6. Emisión SRI Síncrona
            # Intentamos enviar y autorizar en tiempo real
            sri_response = self.sri_service.enviar_factura(factura, cliente)
            
            # Actualizamos datos del SRI siempre que haya respuesta (aunque sea error)
            if sri_response.autorizacion_id:
                factura.clave_acceso_sri = sri_response.autorizacion_id
                clave_acceso_final = sri_response.autorizacion_id

            if sri_response.exito:
                factura.estado_sri = 'AUTORIZADO'
                factura.fecha_autorizacion_sri = timezone.now()
                # Guardamos XML respuesta si es necesario, o el firmado
                if sri_response.xml_respuesta:
                    factura.xml_autorizado_sri = str(sri_response.xml_respuesta)
                estado_sri_final = 'AUTORIZADO'
            else:
                # Si falló (rechazo o error), guardamos el estado real o PENDIENTE para reintento
                # La regla de negocio dice: Si falla, marcar PENDIENTE para que el worker reintente
                factura.estado_sri = 'PENDIENTE' 
                factura.mensaje_error_sri = sri_response.mensaje_error
                # Logueamos advertencia pero NO fallamos la transacción de venta
                print(f"SRI Respuesta No Exitosa: {sri_response.estado} - {sri_response.mensaje_error}")

            factura.save()

        except Exception as e:
            # Captura de errores de conexión/timeout o excepciones internas del servicio
            print(f"Excepción SRI (Venta Offline): {str(e)}")
            # La factura queda en estado default (PENDIENTE) y guardamos el error local
            factura.mensaje_error_sri = f"Error Local SRI: {str(e)}"
            factura.save()

        return {
            "exito": True,
            "factura_id": factura.id,
            "pago_id": pago.id,
            "total_venta": total_venta,
            "items": items_procesados,
            "mensaje": "Venta procesada correctamente.",
            "estado_sri": estado_sri_final,
            "clave_acceso": clave_acceso_final,
            "pdf_url": f"/api/v1/facturas/{factura.id}/pdf/", 
            "xml_url": f"/api/v1/facturas/{factura.id}/xml/"
        }
