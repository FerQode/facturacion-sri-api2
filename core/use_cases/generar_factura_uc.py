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
    ITerrenoRepository
)
from core.interfaces.services import ISRIService 

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
        sri_service: ISRIService 
    ):
        self.factura_repo = factura_repo
        self.lectura_repo = lectura_repo
        self.medidor_repo = medidor_repo
        self.terreno_repo = terreno_repo
        self.socio_repo = socio_repo
        self.sri_service = sri_service 

    @transaction.atomic  # <--- CLAVE: Todo esto es una sola unidad de éxito o fracaso
    def execute(self, input_dto: GenerarFacturaDesdeLecturaDTO) -> Factura:
        
        # 1. IDEMPOTENCIA: ¿Ya existe una factura para esta lectura?
        # Esto previene el error "Duplicate entry" si se reintenta el proceso.
        factura_existente = self.factura_repo.get_by_lectura_id(input_dto.lectura_id)
        
        if factura_existente:
            print(f"⚠️ AVISO: Retomando factura existente ID {factura_existente.id} para lectura {input_dto.lectura_id}")
            factura = factura_existente
            
            # Recuperamos el socio para el reenvío al SRI
            socio = self.socio_repo.get_by_id(factura.socio_id)
            
        else:
            # 2. FLUJO NORMAL: Crear nueva factura
            print(f"✨ Creando nueva factura para lectura {input_dto.lectura_id}")
            
            # --- Validaciones ---
            lectura = self.lectura_repo.get_by_id(input_dto.lectura_id)
            if not lectura: raise LecturaNoEncontradaError(f"Lectura {input_dto.lectura_id} no encontrada.")
            
            # Si la lectura dice "ya facturada" pero no encontramos la factura arriba,
            # es una inconsistencia grave de datos.
            if lectura.esta_facturada: 
                raise ValidacionError(f"La lectura {lectura.id} figura como procesada, pero no se encontró su factura.")

            medidor = self.medidor_repo.get_by_id(lectura.medidor_id)
            if not medidor: raise MedidorNoEncontradoError("Medidor no encontrado.")
            terreno = self.terreno_repo.get_by_id(medidor.terreno_id)
            if not terreno: raise ValidacionError("Terreno no encontrado.")
            socio = self.socio_repo.get_by_id(terreno.socio_id)
            if not socio: raise ValidacionError("Socio no encontrado.")

            # --- Creación de Entidad ---
            factura = Factura(
                id=None,
                socio_id=socio.id,
                medidor_id=medidor.id,
                lectura=lectura,
                fecha_emision=input_dto.fecha_emision,
                fecha_vencimiento=input_dto.fecha_vencimiento,
                estado=EstadoFactura.PENDIENTE,
                sri_ambiente=1,
                sri_tipo_emision=1
            )
            
            # --- Cálculos ---
            consumo_entero = int(float(lectura.consumo_del_mes_m3))
            factura.calcular_total_con_medidor(consumo_entero)

            # --- Persistencia Inicial ---
            factura = self.factura_repo.save(factura)

        # 3. INTEGRACIÓN SRI (Se ejecuta tanto para nuevas como para existentes fallidas)
        # Si la factura ya está autorizada, no reintentamos
        if factura.estado_sri == "AUTORIZADO":
            return factura

        try:
            # Intentamos enviar (o re-enviar)
            respuesta_sri = self.sri_service.enviar_factura(factura, socio)
            
            if respuesta_sri.exito:
                factura.sri_clave_acceso = respuesta_sri.autorizacion_id
                factura.sri_xml_autorizado = respuesta_sri.xml_respuesta
                factura.sri_fecha_autorizacion = timezone.now()
                factura.sri_mensaje_error = None
                factura.estado_sri = "AUTORIZADO" 
            else:
                factura.sri_mensaje_error = respuesta_sri.mensaje_error
                factura.sri_clave_acceso = respuesta_sri.autorizacion_id
                factura.estado_sri = "RECHAZADO"

            # Actualizamos la factura con el resultado del SRI
            self.factura_repo.save(factura)

        except Exception as e:
            # Error técnico (Java, Conexión, etc.)
            # Guardamos el error en la factura, pero NO hacemos rollback de la factura creada
            # para que el usuario pueda ver qué pasó y reintentar.
            msg_error = f"Error Técnico SRI: {str(e)}"
            print(f"❌ {msg_error}")
            
            factura.sri_mensaje_error = msg_error
            factura.estado_sri = "ERROR_TECNICO"
            self.factura_repo.save(factura)

        # 4. FINALIZACIÓN
        # Si era nueva, marcamos la lectura como facturada
        if not factura_existente:
            lectura.esta_facturada = True
            self.lectura_repo.save(lectura)
        
        return factura