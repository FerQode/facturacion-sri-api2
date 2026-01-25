
from typing import List, Dict
from decimal import Decimal
from datetime import date

# Imports de tus Entidades de Dominio
from core.domain.factura import Factura
from core.domain.lectura import Lectura
from core.domain.socio import Socio

class FacturacionService:
    """
    Servicio de Dominio puro.
    Responsabilidad: Orquestar el cálculo de Agua + Multas = Total a Pagar.
    No guarda en base de datos, solo calcula.
    """

    def previsualizar_factura(self, lectura: Lectura, socio: Socio, multas_pendientes: List[Dict]) -> Dict:
        """
        Genera el DTO (Diccionario) plano que necesita el Frontend.
        """
        # 1. Instanciamos una Factura Temporal (En memoria)
        factura_temp = Factura(
            id=None,
            socio_id=socio.id,
            medidor_id=lectura.medidor_id,
            fecha_emision=date.today(),
            fecha_vencimiento=date.today(),
            lectura=lectura
        )
        
        # 2. Calcular Consumo de Agua (Usando tu lógica de Tarifa Plana)
        # lectura.valor = Lectura Actual
        # lectura.lectura_anterior = Lectura Anterior
        consumo = lectura.valor - lectura.lectura_anterior
        if consumo < 0: consumo = 0 # Protección de datos
        
        # Esto ejecuta la lógica de los $3.00 base + excedentes
        factura_temp.calcular_total_con_medidor(int(consumo))
        
        monto_agua = factura_temp.total # Guardamos el subtotal solo del agua

        # 3. Sumar las Multas Pendientes
        total_multas = Decimal("0.00")
        nombres_multas = []
        
        for multa in multas_pendientes:
            valor = Decimal(str(multa['valor']))
            # Agregamos la multa al objeto factura para que sume al total
            factura_temp.agregar_multa(multa['motivo'], valor)
            
            total_multas += valor
            nombres_multas.append(multa['motivo'])

        # 4. Retornar el JSON exacto que pidió tu compañero
        return {
            "id": lectura.id, # Usamos el ID de la lectura como referencia temporal
            "fecha_lectura": lectura.fecha,
            # Nota: Si lectura tiene el codigo inyectado, úsalo, sino usa el ID
            "medidor_codigo": getattr(lectura, 'medidor_codigo', str(lectura.medidor_id)),
            "socio_nombre": f"{socio.nombres} {socio.apellidos}",
            "cedula": socio.cedula,
            
            "lectura_anterior": float(lectura.lectura_anterior),
            "lectura_actual": float(lectura.valor),
            "consumo": float(consumo),
            
            "monto_agua": float(monto_agua),
            "multas_mingas": float(total_multas),
            "detalle_multas": nombres_multas, # Array de strings
            
            "total_pagar": float(factura_temp.total)
        }