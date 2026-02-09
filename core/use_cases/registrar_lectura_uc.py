# core/use_cases/registrar_lectura_uc.py

from core.domain.lectura import Lectura
from core.interfaces.repositories import ILecturaRepository, IMedidorRepository
# ✅ CORRECCIÓN 1: Importamos desde el archivo correcto donde definimos el DTO
from core.use_cases.lectura_dtos import RegistrarLecturaDTO
from core.shared.exceptions import MedidorNoEncontradoError, BusinessRuleException

class RegistrarLecturaUseCase:
    """
    Caso de Uso: Registrar Lectura.
    Responsabilidad: Recibir 'lectura_actual', validar contra la anterior
    y guardar como 'valor' en la entidad.
    """
    def __init__(self, lectura_repo: ILecturaRepository, medidor_repo: IMedidorRepository):
        self.lectura_repo = lectura_repo
        self.medidor_repo = medidor_repo

    # ✅ CORRECCIÓN 2: El método debe llamarse 'ejecutar' porque así lo llama la Vista
    def ejecutar(self, input_dto: RegistrarLecturaDTO) -> Lectura:
        
        # 1. Validar que el medidor existe
        medidor = self.medidor_repo.get_by_id(input_dto.medidor_id)
        if not medidor:
             # Nota: Si tu sistema maneja estado, puedes descomentar la validación de 'ACTIVO'
             # if medidor.estado != 'ACTIVO': ...
            raise MedidorNoEncontradoError(f"Medidor {input_dto.medidor_id} no existe.")

        # 2. Obtener la última lectura para determinar la base de cálculo
        ultima_lectura = self.lectura_repo.get_latest_by_medidor(input_dto.medidor_id)
        
        lectura_anterior_valor = medidor.lectura_inicial
        if ultima_lectura:
            lectura_anterior_valor = float(ultima_lectura.valor)

        # ✅ CORRECCIÓN 3: Leemos el campo correcto del DTO ('lectura_actual')
        lectura_actual = float(input_dto.lectura_actual)

        # 3. REGLA DE NEGOCIO: Validación de Consistencia
        if lectura_actual < lectura_anterior_valor:
            raise BusinessRuleException(
                f"Error de Lectura: La lectura actual ({lectura_actual}) "
                f"no puede ser menor a la lectura anterior ({lectura_anterior_valor})."
            )

        # 4. Cálculo del Consumo (Lógica de Negocio)
        consumo_calculado = lectura_actual - lectura_anterior_valor
        consumo_calculado = round(consumo_calculado, 2)

        # 5. Crear la Entidad de Dominio (Mapeo Final)
        # Aquí convertimos el término de Frontend (lectura_actual) al de Dominio (valor)
        nueva_lectura = Lectura(
            id=None,
            medidor_id=input_dto.medidor_id,
            
            valor=lectura_actual, # <--- Mapeo clave
            
            fecha=input_dto.fecha_lectura,
            lectura_anterior=lectura_anterior_valor,
            
            # Si tu Entidad Lectura tiene este campo, lo asignamos aquí.
            # Si la entidad calcula esto sola en su __post_init__, puedes omitirlo, 
            # pero pasarlo explícito es más seguro.
            consumo_del_mes_m3=consumo_calculado, 
            
            observacion=input_dto.observacion,
            
            # Datos de auditoría si los tienes
            # operador_id=input_dto.operador_id 
        )
        
        # 6. Persistir
        lectura_guardada = self.lectura_repo.save(nueva_lectura)
        
        return lectura_guardada