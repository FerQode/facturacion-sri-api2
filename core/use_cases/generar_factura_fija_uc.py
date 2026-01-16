from datetime import date
from django.db import transaction

# Imports de Modelos
from adapters.infrastructure.models.factura_model import FacturaModel, DetalleFacturaModel
from adapters.infrastructure.models.servicio_model import ServicioModel
from core.shared.enums import EstadoFactura

class GenerarFacturaFijaUseCase:
    """
    Generador Masivo de Facturas para Tarifa Fija (Sin Medidor).
    Diseñado para ejecución mensual ("Cierre de Mes").
    """

    def ejecutar(self, fecha_emision: date = None):
        """
        Genera facturas solo para servicios FIJOS activos que no hayan sido facturados este mes.
        """
        if not fecha_emision:
            fecha_emision = date.today()

        # 1. Obtener servicios fijos activos para procesar
        servicios_fijos = ServicioModel.objects.filter(
            tipo='FIJO',
            activo=True
        ).select_related('socio', 'terreno')

        reporte = {
            "total_servicios": servicios_fijos.count(),
            "creadas": 0,
            "omitidas": 0,  # Ya existían
            "errores": []   # Fallos técnicos
        }

        # Iteramos socio por socio
        for servicio in servicios_fijos:
            # Usamos atomic AQUÍ para que si falla uno, no tumbe el proceso entero.
            # "Best Effort Strategy"
            try:
                with transaction.atomic():
                    # 2. Evitar duplicados: ¿Ya existe factura para este servicio este mes?
                    ya_existe = FacturaModel.objects.filter(
                        servicio=servicio,
                        fecha_emision__year=fecha_emision.year,
                        fecha_emision__month=fecha_emision.month,
                        estado__in=[EstadoFactura.PENDIENTE.value, EstadoFactura.PAGADA.value]
                    ).exists()

                    if ya_existe:
                        reporte["omitidas"] += 1
                        continue 

                    # 3. Crear Cabecera de Factura
                    factura = FacturaModel.objects.create(
                        socio=servicio.socio,
                        servicio=servicio,
                        medidor=None,  # Explícito: No hay medidor
                        lectura=None,  # Explícito: No hay lectura
                        fecha_emision=fecha_emision,
                        fecha_vencimiento=fecha_emision, # Política: Vence el mismo día o +30
                        estado=EstadoFactura.PENDIENTE.value,
                        
                        # Valores Monetarios
                        subtotal=servicio.valor_tarifa,
                        impuestos=0,
                        total=servicio.valor_tarifa,
                        
                        # Datos SRI Pre-cargados (Listos para cuando se cobre)
                        sri_ambiente=1,      # 1: Pruebas (Debería venir de settings)
                        sri_tipo_emision=1   # 1: Normal
                    )

                    # 4. Crear Detalle Único
                    DetalleFacturaModel.objects.create(
                        factura=factura,
                        concepto="Servicio de Agua Potable (Tarifa Fija)",
                        cantidad=1,
                        precio_unitario=servicio.valor_tarifa,
                        subtotal=servicio.valor_tarifa
                    )

                    reporte["creadas"] += 1

            except Exception as e:
                # Capturamos el error, lo agregamos al reporte y CONTINUAMOS con el siguiente
                msg_error = f"Servicio ID {servicio.id} (Socio: {servicio.socio.cedula}): {str(e)}"
                reporte["errores"].append(msg_error)

        return reporte