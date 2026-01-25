# core>use_cases>generar_factura_fija_uc.py
from datetime import date, timedelta
from typing import Dict, List, Any

# Domain
from core.domain.factura import Factura, EstadoFactura, DetalleFactura, TARIFA_FIJA_SIN_MEDIDOR
from core.interfaces.repositories import IFacturaRepository, IServicioRepository

class GenerarFacturaFijaUseCase:
    """
    Generador Masivo de Facturas para Tarifa Fija (Sin Medidor).
    Refactorizado con Clean Architecture (Sin dependencias de Framework).
    """

    def __init__(self, factura_repo: IFacturaRepository, servicio_repo: IServicioRepository):
        self.factura_repo = factura_repo
        self.servicio_repo = servicio_repo

    def ejecutar(self, anio: int = None, mes: int = None, fecha_emision: date = None) -> Dict[str, Any]:
        """
        Genera facturas para un PERIODO FISCAL específico (anio/mes).
        Si no se especifican, se asume el mes actual.
        """
        if not fecha_emision:
            fecha_emision = date.today()
        
        # Defaults a fecha actual si no se envia periodo fiscal
        if not anio: anio = fecha_emision.year
        if not mes: mes = fecha_emision.month

        fecha_vencimiento = fecha_emision + timedelta(days=15)

        # 1. Obtener servicios fijos activos para procesar (Delegado al repositorio)
        servicios_fijos = self.servicio_repo.obtener_servicios_fijos_activos()

        reporte = {
            "periodo_fiscal": f"{anio}-{mes}",
            "fecha_emision": str(fecha_emision),
            "total_servicios": len(servicios_fijos),
            "creadas": 0,
            "omitidas": 0,   # Ya existían
            "errores": []    # Fallos técnicos
        }

        for servicio in servicios_fijos:
            try:
                # 2. Evitar duplicados (Delegado al repositorio usando el periodo estricto)
                if self.factura_repo.existe_factura_fija_mes(servicio.id, anio, mes):
                    reporte["omitidas"] += 1
                    continue

                # 3. Construir Agregado de Factura (Dominio Puro)
                nuev_factura = Factura(
                    id=None,
                    socio_id=servicio.socio.id,
                    servicio_id=servicio.id,
                    medidor_id=None,
                    fecha_emision=fecha_emision,
                    fecha_vencimiento=fecha_vencimiento,
                    anio=anio,  # Periodo Fiscal Estricto
                    mes=mes,    # Periodo Fiscal Estricto
                    estado=EstadoFactura.PENDIENTE,
                    detalles=[],
                    # SRI Defaults (se pueden mover a config o servicio)
                    sri_ambiente=1,
                    sri_tipo_emision=1
                )

                # 4. Calcular Totales (Lógica de Negocio del Dominio)
                nuev_factura.calcular_total_sin_medidor()

                # 5. Persistencia (Repositorio)
                self.factura_repo.guardar(nuev_factura)

                reporte["creadas"] += 1

            except Exception as e:
                # Identificación del error
                identificacion = getattr(servicio.socio, 'identificacion', 'Unknown')
                msg_error = f"Servicio ID {servicio.id} (Socio: {identificacion}): {str(e)}"
                reporte["errores"].append(msg_error)

        return reporte