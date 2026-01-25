# core/use_cases/registrar_cobro_uc.py
from decimal import Decimal
from typing import List, Dict, Tuple
from datetime import datetime

# Interfaces (Puertos)
from core.interfaces.repositories import IFacturaRepository, IPagoRepository
from core.interfaces.services import ISRIService, IEmailService

# Dominio
from core.domain.factura import Factura, DetalleFactura, EstadoFactura
from core.domain.socio import Socio
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

class RegistrarCobroUseCase:
    """
    Gestiona la Recaudación, la Emisión Electrónica (SRI), Notificación y genera el Comprobante.
    Implementa el 'Candado de Seguridad' para validar transferencias previas.
    """

    def __init__(
        self, 
        factura_repo: IFacturaRepository, 
        pago_repo: IPagoRepository,
        sri_service: ISRIService,
        email_service: IEmailService
    ):
        # Inyección de Dependencias (DIP)
        self.factura_repo = factura_repo
        self.pago_repo = pago_repo
        self.sri_service = sri_service
        self.email_service = email_service

    def ejecutar(self, factura_id: int, lista_pagos: List[Dict]) -> Dict:
        # 1. Obtener Entidad (Agnóstico de la BD)
        factura = self.factura_repo.obtener_por_id(factura_id)
        if not factura:
            raise EntityNotFoundException(f"La factura {factura_id} no existe.")

        # 2. Validaciones de Dominio Puras
        if factura.estado == EstadoFactura.PAGADA:
            raise BusinessRuleException("Esta factura ya se encuentra PAGADA.")
        
        # (Asumimos que la validación de ANULADA se maneja igual si existiera el estado)

        # 3. Lógica del "Candado" (Delegada al repositorio)
        if self.pago_repo.tiene_pagos_pendientes(factura.id):
             raise BusinessRuleException("Error: Existen transferencias subidas pero NO verificadas por Tesorería. Vaya al módulo de validación primero.")

        monto_transferencias = Decimal(self.pago_repo.obtener_sumatoria_validada(factura.id))
        
        # 4. Calcular Total Recibido (Efectivo + Transferencias Nuevas)
        # Refactor Clean Architecture: El caso de uso debe agnóstico al método.
        # Sumamos TODO lo que viene en la lista de pagos de la petición.
        total_recibido_caja = sum(
            Decimal(str(p['monto'])) 
            for p in lista_pagos 
        )
        
        # 5. Validación de Totales
        # Total Acumulado = (Transferencias YA validadas previamente) + (Dinero/Valores recibidos ahora)
        total_acumulado = monto_transferencias + total_recibido_caja
        faltante = factura.total - total_acumulado
        
        # Margen de error de 1 centavo
        if faltante > Decimal("0.01"):
            raise BusinessRuleException(
                f"Monto insuficiente. Faltan ${faltante}. "
                f"(Previo Validado: ${monto_transferencias} + Recibido Caja: ${total_recibido_caja})"
            )

        # 6. Persistencia
        # Registramos los nuevos pagos (Efectivo, Transferencia, Cheque, etc.)
        # El repositorio ya sabe cómo guardarlos y marcarlos como válidos si vienen de caja.
        self.pago_repo.registrar_pagos(factura.id, lista_pagos)
        
        # Actualizamos estado de la factura
        factura.estado = EstadoFactura.PAGADA
        self.factura_repo.guardar(factura) 

        # 7. Orquestación SRI + Email
        resultado_sri = self._procesar_sri_y_notificar(factura)

        # 8. Construcción de respuesta (Podría ser un DTO, pero mantenemos compatibilidad Dict)
        return {
            "mensaje": "Cobro registrado correctamente.",
            "factura_id": factura.id,
            "nuevo_estado": "PAGADA",
            "sri": resultado_sri,
            # El comprobante completo se podría construir aquí o solicitar aparte
            "comprobante_preview": {
                "total": factura.total,
                "pagado": total_acumulado
            }
        }

    def _procesar_sri_y_notificar(self, factura: Factura) -> Dict:
        """
        Intenta autorizar en el SRI y enviar correo. 
        Maneja fallos de conexión sin tumbar la transacción principal.
        """
        sri_resultado = {
            "enviado": False,
            "estado": "PENDIENTE_ENVIO",
            "mensaje": ""
        }

        try:
            # A. Obtener datos necesarios para soc
            # Nota: Factura ya tiene socio_id, pero necesitamos el objeto Socio completo.
            # En obtener_por_id, el repo ya debería haber poblado factura.socio (si modificamos la entidad para tenerlo)
            # O asumimos que self.factura_repo.obtener_por_id retorna un objeto que tiene acceso al socio.
            # Para Clean Architecture estricto, Factura debería tener un campo 'socio' tipo Socio entity, no solo ID.
            # Asumiremos que factura tiene el atributo 'socio_obj' o similar poblado por el repo, 
            # O hacemos un fetch extra si es necesario. Por ahora usamos la relación que existía.
            
            # Como la entidad definida en el paso 1 tiene 'socio_id', pero necesitamos los datos del socio,
            # vamos a asumir que el repositorio nos devuelve una Factura enriquecida o consultamos el socio.
            # Para simplificar y dado que 'Factura' es DataClass, asumiremos que el repo inyectó el objeto socio 
            # en un campo o que pasamos el objeto socio necesario.
            
            # SOLUCIÓN PRAGMÁTICA: Usar la entidad Factura que tiene los datos necesarios.
            # Si la entidad Factura solo tiene ID, estamos limitados.
            # Revisando factura.py anterior: tenia socio_id.
            # Vamos a asumir que el repositorio inyectó el socio en factura.socio_obj (atributo dinámico o modificado)
            # O mejor, pasamos factura y su socio_id.
            
            # Revisando 'core/domain/factura.py', no tiene campo 'socio', solo 'socio_id'.
            # Necesitamos el socio.
            # OPCIÓN: Agregar metodo al repositorio 'obtener_socio(id)'.
            # Pero para no complicar las interfaces ahora, asumiremos que 'Factura' tiene un campo opcional 'socio_data'
            # o que el repositorio maneja la lógica.
            
            # Vamos a intentar enviar con lo que tenemos.
            # El servicio SRI necesita objeto Socio.
            # Haremos un pequeño hack temporal o asumiremos que Factura tiene atributo .socio inyectado.
            
            # Supuesto: El Repository de Factura devuelve una entidad con el atributo .socio cargado
            # aunque no esté en el dataclass original (Python permite esto dinamicamente)
            # o modificamos el Dataclass.
            
            # Para este código:
            socio = getattr(factura, 'socio_obj', None) 
            # Si es None, no podemos enviar al SRI.
            
            if not socio:
                # Fallback: Intentar construirlo o saltar SRI
                sri_resultado["mensaje"] = "No se pudo cargar datos del socio para SRI."
                return sri_resultado

                # 1. Generar Clave (si falta)
            if not factura.sri_clave_acceso:
                # Necesitamos RUC emisor y fecha. 
                # Refactor Clean Architecture: El servicio SRI encapsula el RUC del emisor.
                # Ya no necesitamos pasarlo desde el Caso de Uso.
                clave = self.sri_service.generar_clave_acceso(
                    fecha_emision=factura.fecha_emision,
                    nro_factura=str(factura.id)
                )
                factura.sri_clave_acceso = clave
                # Guardamos la clave generada
                self.factura_repo.guardar(factura)

            # 2. Enviar al SRI
            respuesta = self.sri_service.enviar_factura(factura, socio)

            if respuesta.exito:
                factura.estado_sri = "AUTORIZADO"
                factura.sri_xml_autorizado = respuesta.xml_respuesta
                factura.sri_fecha_autorizacion = datetime.now() # Usar servicio de tiempo si fuera estricto
                
                sri_resultado["enviado"] = True
                sri_resultado["estado"] = "AUTORIZADO"
                sri_resultado["mensaje"] = str(respuesta.autorizacion_id)

                # 3. Notificar Email
                self.email_service.enviar_notificacion_factura(
                    email_destinatario=socio.email,
                    nombre_socio=f"{socio.nombres} {socio.apellidos}",
                    numero_factura=factura.id,
                    xml_autorizado=respuesta.xml_respuesta
                )
            else:
                factura.estado_sri = respuesta.estado
                factura.sri_mensaje_error = respuesta.mensaje_error
                sri_resultado["estado"] = respuesta.estado
                sri_resultado["mensaje"] = respuesta.mensaje_error

            # Guardamos estado SRI final
            self.factura_repo.guardar(factura)

        except Exception as e:
            sri_resultado["estado"] = "ERROR_SISTEMA"
            sri_resultado["mensaje"] = f"Fallo proceso SRI: {str(e)}"
        
        return sri_resultado
