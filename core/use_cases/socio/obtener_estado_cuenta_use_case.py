# core/use_cases/socio/obtener_estado_cuenta_use_case.py
from typing import List, Optional
from core.interfaces.repositories import ISocioRepository, ITerrenoRepository, IFacturaRepository, IPagoRepository, IServicioRepository
from core.domain.dtos import EstadoCuentaDTO, SocioResumenDTO, ResumenFinancieroDTO, PropiedadDTO, DeudaDTO, ObligacionGeneralDTO, PagoHistorialDTO
from core.shared.enums import EstadoFactura

class ObtenerEstadoCuentaUseCase:
    def __init__(self, 
                 socio_repo: ISocioRepository, 
                 terreno_repo: ITerrenoRepository, 
                 factura_repo: IFacturaRepository, 
                 pago_repo: IPagoRepository,
                 servicio_repo: IServicioRepository):
        self.socio_repo = socio_repo
        self.terreno_repo = terreno_repo
        self.factura_repo = factura_repo
        self.pago_repo = pago_repo
        self.servicio_repo = servicio_repo

    def execute(self, socio_id: int) -> EstadoCuentaDTO:
        # 1. Recuperar info básica del socio
        socio = self.socio_repo.get_by_id(socio_id)
        if not socio:
            raise ValueError(f"Socio {socio_id} no encontrado")

        socio_dto = SocioResumenDTO(
            nombres=f"{socio.nombres} {socio.apellidos}",
            identificacion=socio.identificacion,
            email=socio.email or ""
        )

        # 2. Recuperar Infraestructura (Terrenos y Servicios)
        terrenos = self.terreno_repo.get_by_socio(socio_id)
        servicios_raw = self.servicio_repo.get_by_socio(socio_id) # List[dict: id, terreno_id, tipo]
        
        # Mapa: ServicioID -> TerrenoID
        map_servicio_terreno = {s['id']: s['terreno_id'] for s in servicios_raw}
        # Mapa: TerrenoID -> Info extra del servicio (ej. Tipo)
        map_terreno_tipo = {s['terreno_id']: s['tipo'] for s in servicios_raw}

        # 3. Recuperar Facturas Pendientes
        facturas_pendientes = self.factura_repo.obtener_pendientes_por_socio(socio_id)
        
        # 4. Agrupar logicamente
        propiedades_map = {} # TerrenoID -> PropiedadDTO
        obligaciones_generales = []
        
        total_deuda = 0.0
        cantidad_facturas = 0
        
        # Inicializar Propiedades DTO basándonos en Terrenos
        for t in terrenos:
            tipo_srv = map_terreno_tipo.get(t.id, "SIN SERVICIO")
            propiedades_map[t.id] = PropiedadDTO(
                id=t.id,
                direccion=t.direccion or "Sin Dirección",
                tipo_servicio=tipo_srv,
                medidor=None, # Idealmente buscar medidor si es medido
                deudas=[]
            )

        # Clasificar Facturas
        for f in facturas_pendientes:
            total_deuda += float(f.total)
            cantidad_facturas += 1
            
            # Construir detalle de deuda
            concepto = f.detalles[0].concepto if f.detalles else "Consumo"
            # Extraer consumo si existe (heuristic)
            consumo_m3 = None
            if "Consumo Excedente" in concepto or "Servicio Base" in concepto:
                # Podríamos intentar parsear o usar f.lectura
                pass 

            deuda_dto = DeudaDTO(
                factura_id=f.id,
                periodo=f"{f.mes}/{f.anio}",
                detalle=concepto,
                valor=f.total,
                consumo_m3=consumo_m3,
                archivo_xml=f.archivo_xml_path, # Usamos la ruta del archivo si existe
                archivo_pdf=f.archivo_pdf # Usamos la ruta URL mapeada
            )
            
            # Lógica de asignación
            terreno_id = map_servicio_terreno.get(f.servicio_id)
            
            if terreno_id and terreno_id in propiedades_map:
                propiedades_map[terreno_id].deudas.append(deuda_dto)
            else:
                # Es Obligación General (Multa, o Servicio de un terreno ya no asociado?)
                obligaciones_generales.append(ObligacionGeneralDTO(
                    factura_id=f.id,
                    tipo="MULTA" if "Multa" in concepto else "OTROS",
                    concepto=concepto,
                    fecha_evento=None,
                    valor=f.total
                ))

        # 5. Recuperar Historial de Pagos
        ultimos_pagos_raw = self.pago_repo.obtener_ultimos_pagos(socio_id, limite=5)
        historial_pagos = [
            PagoHistorialDTO(
                fecha=p['fecha'],
                monto=p['monto'],
                recibo_nro=p['recibo_nro'],
                archivo_pdf=p['archivo_pdf']
            ) for p in ultimos_pagos_raw
        ]

        # 6. Ensamblar Respuesta
        resumen = ResumenFinancieroDTO(
            total_deuda=total_deuda,
            cantidad_facturas_pendientes=cantidad_facturas
        )
        
        return EstadoCuentaDTO(
            socio=socio_dto,
            resumen_financiero=resumen,
            propiedades=list(propiedades_map.values()),
            obligaciones_generales=obligaciones_generales,
            historial_pagos_recientes=historial_pagos
        )
