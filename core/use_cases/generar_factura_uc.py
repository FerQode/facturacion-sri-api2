# core/use_cases/generar_factura_uc.py

from datetime import date
from decimal import Decimal
from typing import Optional
from django.utils import timezone

# Django Transaction (Para atomicidad real)
from django.db import transaction

# Dominio
from core.domain.factura import Factura
from core.shared.enums import EstadoFactura
from core.shared.exceptions import (
    LecturaNoEncontradaError,
    MedidorNoEncontradoError,
    ValidacionError
)

# Interfaces
from core.interfaces.repositories import (
    IFacturaRepository,
    ILecturaRepository,
    IMedidorRepository,
    ISocioRepository,
    ITerrenoRepository,
    IServicioRepository,
    IGobernanzaRepository # ✅ Nuevo Dependency Fase 3
)

# DTOs
from core.use_cases.dtos import GenerarFacturaDesdeLecturaDTO

class GenerarFacturaDesdeLecturaUseCase:
    """
    Caso de Uso Robusto: Generación de Factura con Idempotencia y Atomicidad.
    """

    def __init__(
        self,
        factura_repo: IFacturaRepository,
        lectura_repo: ILecturaRepository,
        medidor_repo: IMedidorRepository,
        terreno_repo: ITerrenoRepository,
        socio_repo: ISocioRepository,
        servicio_repo: IServicioRepository,
        gobernanza_repo: IGobernanzaRepository, # ✅ Inject Repo
    ):
        self.factura_repo = factura_repo
        self.lectura_repo = lectura_repo
        self.medidor_repo = medidor_repo
        self.terreno_repo = terreno_repo
        self.socio_repo = socio_repo
        self.servicio_repo = servicio_repo
        self.gobernanza_repo = gobernanza_repo


    @transaction.atomic
    def execute(self, input_dto: GenerarFacturaDesdeLecturaDTO) -> Factura:

        # 1. IDEMPOTENCIA
        factura_existente = self.factura_repo.get_by_lectura_id(input_dto.lectura_id)
        if factura_existente:
            return factura_existente

        # 2. VALIDACIONES Y CREACIÓN
        lectura = self.lectura_repo.get_by_id(input_dto.lectura_id)
        if not lectura: raise LecturaNoEncontradaError(f"Lectura {input_dto.lectura_id} no encontrada.")

        if lectura.esta_facturada:
            raise ValidacionError(f"La lectura {lectura.id} ya figura como procesada.")

        medidor = self.medidor_repo.get_by_id(lectura.medidor_id)
        if not medidor: raise MedidorNoEncontradoError("Medidor no encontrado.")
        terreno = self.terreno_repo.get_by_id(medidor.terreno_id)
        if not terreno: raise ValidacionError("Terreno no encontrado.")
        socio = self.socio_repo.get_by_id(terreno.socio_id)
        if not socio: raise ValidacionError("Socio no encontrado.")

        # 3. INSTANCIAR FACTURA (ESTADO PENDIENTE)
        factura = Factura(
            id=None,
            socio_id=socio.id,
            medidor_id=medidor.id,
            lectura=lectura,
            fecha_emision=input_dto.fecha_emision,
            fecha_vencimiento=input_dto.fecha_vencimiento,
            estado=EstadoFactura.PENDIENTE, # Nace debiendo

            # SRI: Limpios
            sri_ambiente=1,
            sri_tipo_emision=1,
            sri_clave_acceso=None,
            sri_xml_autorizado=None,
            sri_mensaje_error=None,
            estado_sri="PENDIENTE_ENVIO" # Indicador para el cajero
        )

        # 4. CÁLCULOS
        # 4.1 Obtener Contrato de Servicio (Tarifas Dinámicas)
        servicio = self.servicio_repo.get_active_by_terreno_and_type(terreno.id, 'MEDIDO')
        
        # Defaults de Respaldo
        tarifa_base_m3 = 15
        tarifa_base_precio = Decimal("3.00")
        tarifa_excedente_precio = Decimal("0.25")
        
        if servicio:
            # Factura Enlazada al Servicio (Para reportes)
            factura.servicio_id = servicio.id
            
            # Usar valores de la DB
            tarifa_base_m3 = servicio.tarifa_basica_m3
            tarifa_base_precio = servicio.valor_tarifa 
            tarifa_excedente_precio = servicio.tarifa_excedente_precio

        consumo_entero = int(float(lectura.consumo_del_mes_m3))
        
        # 4.2 Calcular usando parámetros
        factura.calcular_total_con_medidor(
            consumo_m3=consumo_entero,
            tarifa_base_m3=tarifa_base_m3,
            tarifa_base_precio=tarifa_base_precio,
            tarifa_excedente_precio=tarifa_excedente_precio
        )

        # 4.3 PROCESAR MULTAS PENDIENTES (FASE 3)
        multas_pendientes = self.gobernanza_repo.obtener_multas_pendientes(socio.id)
        if multas_pendientes:
            for multa in multas_pendientes:
                # Agregar al detalle de la factura
                concepto = f"Multa: {multa.evento.nombre} ({multa.evento.fecha})"
                valor = multa.evento.valor_multa
                
                factura.agregar_multa(concepto, valor)

        # 5. GUARDAR
        factura = self.factura_repo.save(factura)

        # 5.1 VINCULAR MULTAS A LA FACTURA CREADA
        if multas_pendientes:
            for multa in multas_pendientes:
                self.gobernanza_repo.marcar_multa_como_facturada(multa.id, factura.id)

        # 6. CERRAR LECTURA
        lectura.esta_facturada = True
        self.lectura_repo.save(lectura)

        return factura