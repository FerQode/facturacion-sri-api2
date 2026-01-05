from core.domain.lectura import Lectura
from core.interfaces.repositories import ILecturaRepository, IMedidorRepository
from core.use_cases.dtos import RegistrarLecturaDTO
from core.shared.exceptions import MedidorNoEncontradoError

class RegistrarLecturaUseCase:
    """
    Caso de Uso: Registrar Lectura.
    Responsabilidad: Orquestar la obtención de datos previos, CALCULAR el consumo 
    de forma inmutable y persistir la transacción.
    """
    def __init__(self, lectura_repo: ILecturaRepository, medidor_repo: IMedidorRepository):
        self.lectura_repo = lectura_repo
        self.medidor_repo = medidor_repo

    def execute(self, input_dto: RegistrarLecturaDTO) -> Lectura:
        # 1. Validar que el medidor existe y está activo
        medidor = self.medidor_repo.get_by_id(input_dto.medidor_id)
        if not medidor or medidor.estado != 'ACTIVO':
            raise MedidorNoEncontradoError(f"Medidor {input_dto.medidor_id} no existe o está inactivo.")

        # 2. Obtener la última lectura para determinar la base de cálculo
        ultima_lectura = self.lectura_repo.get_latest_by_medidor(input_dto.medidor_id)
        
        lectura_anterior_valor = 0.0
        if ultima_lectura:
            lectura_anterior_valor = ultima_lectura.valor

        # --- CORRECCIÓN CRÍTICA ---
        # Convertimos el Decimal del DTO a float de Python para poder operar
        lectura_actual = float(input_dto.lectura_actual_m3)

        # 3. REGLA DE NEGOCIO: Validación de Consistencia
        # Usamos la variable convertida 'lectura_actual'
        if lectura_actual < lectura_anterior_valor:
            raise ValueError(
                f"Error de Lectura: El valor actual ({lectura_actual}) "
                f"no puede ser menor a la lectura anterior ({lectura_anterior_valor})."
            )

        # 4. REGLA DE NEGOCIO: Cálculo Inmutable del Consumo
        # Ahora float - float funciona perfecto
        consumo_calculado = lectura_actual - lectura_anterior_valor
        consumo_calculado = round(consumo_calculado, 2) 

        # 5. Crear la Entidad de Dominio (Snapshot Completo)
        nueva_lectura = Lectura(
            id=None,
            medidor_id=input_dto.medidor_id,
            fecha=input_dto.fecha_lectura,
            
            # Bloque Inmutable (Usamos el valor convertido)
            valor=lectura_actual,
            lectura_anterior=lectura_anterior_valor,
            consumo_del_mes_m3=consumo_calculado,
            
            observacion=input_dto.observacion
        )
        
        # 6. Persistir
        lectura_guardada = self.lectura_repo.save(nueva_lectura)
        
        return lectura_guardada