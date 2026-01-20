from datetime import date, timedelta # #### Añadido timedelta
from django.db import transaction

# Imports de Modelos
from adapters.infrastructure.models.factura_model import FacturaModel, DetalleFacturaModel
from adapters.infrastructure.models.servicio_model import ServicioModel
from core.shared.enums import EstadoFactura
# #### Importamos la tarifa oficial del dominio
from core.domain.factura import TARIFA_FIJA_SIN_MEDIDOR

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

        # #### Definimos fecha de vencimiento (ej. 15 días después)
        fecha_vencimiento = fecha_emision + timedelta(days=15)

        # 1. Obtener servicios fijos activos para procesar
        servicios_fijos = ServicioModel.objects.filter(
            tipo='FIJO',
            activo=True
        ).select_related('socio', 'terreno')

        reporte = {
            "total_servicios": servicios_fijos.count(),
            "creadas": 0,
            "omitidas": 0,   # Ya existían
            "errores": []    # Fallos técnicos
        }

        for servicio in servicios_fijos:
            try:
                with transaction.atomic():
                    # 2. Evitar duplicados
                    ya_existe = FacturaModel.objects.filter(
                        servicio=servicio,
                        fecha_emision__year=fecha_emision.year,
                        fecha_emision__month=fecha_emision.month,
                        estado__in=[EstadoFactura.PENDIENTE.value, EstadoFactura.PAGADA.value]
                    ).exists()

                    if ya_existe:
                        reporte["omitidas"] += 1
                        continue

                    # #### Usamos la tarifa acordada de $5.00 (TARIFA_FIJA_SIN_MEDIDOR)
                    valor_a_cobrar = 5.00

                    # 3. Crear Cabecera de Factura
                    factura = FacturaModel.objects.create(
                        socio=servicio.socio,
                        servicio=servicio,
                        medidor=None,
                        lectura=None,
                        fecha_emision=fecha_emision,
                        fecha_vencimiento=fecha_vencimiento, # #### Fecha ajustada
                        estado=EstadoFactura.PENDIENTE.value,

                        # Valores Monetarios
                        subtotal=valor_a_cobrar,
                        impuestos=0,
                        total=valor_a_cobrar,

                        # Datos SRI
                        sri_ambiente=1,
                        sri_tipo_emision=1
                    )

                    # 4. Crear Detalle Único
                    DetalleFacturaModel.objects.create(
                        factura=factura,
                        concepto="Servicio de Agua Potable (Tarifa Fija Mensual)",
                        cantidad=1,
                        precio_unitario=valor_a_cobrar,
                        subtotal=valor_a_cobrar
                    )

                    reporte["creadas"] += 1

            except Exception as e:
                msg_error = f"Servicio ID {servicio.id} (Socio: {servicio.socio.cedula}): {str(e)}"
                reporte["errores"].append(msg_error)

        return reporte