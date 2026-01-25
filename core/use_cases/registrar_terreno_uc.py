from typing import Optional
from core.interfaces.repositories import (
    ITerrenoRepository,
    IMedidorRepository,
    ISocioRepository,
    IBarrioRepository,
    IServicioRepository  # #### 1. Necesitamos el repositorio de servicios
)

from core.domain.terreno import Terreno
from core.domain.medidor import Medidor
# #### 2. Importamos la constante oficial del dominio
from core.domain.factura import TARIFA_FIJA_SIN_MEDIDOR

from core.use_cases.terreno_dtos import RegistrarTerrenoDTO
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

class RegistrarTerrenoUseCase:
    def __init__(self,
                 terreno_repo: ITerrenoRepository,
                 medidor_repo: IMedidorRepository,
                 socio_repo: ISocioRepository,
                 barrio_repo: IBarrioRepository,
                 servicio_repo: IServicioRepository): # #### 3. Inyectamos el servicio
        self.terreno_repo = terreno_repo
        self.medidor_repo = medidor_repo
        self.socio_repo = socio_repo
        self.barrio_repo = barrio_repo
        self.servicio_repo = servicio_repo # #### 4. Asignamos el repositorio

    def ejecutar(self, dto: RegistrarTerrenoDTO) -> Terreno:
        # 1. Validar que el Socio existe
        if not self.socio_repo.get_by_id(dto.socio_id):
            raise EntityNotFoundException(f"El socio con ID {dto.socio_id} no existe.")

        # 2. Validar que el Barrio existe
        if not self.barrio_repo.get_by_id(dto.barrio_id):
            raise EntityNotFoundException(f"El barrio con ID {dto.barrio_id} no existe.")

        # 3. Validaciones de Negocio para el Medidor
        if dto.tiene_medidor:
            if not dto.codigo_medidor:
                raise BusinessRuleException("Si el terreno tiene medidor, el código es obligatorio.")

            medidor_existente = self.medidor_repo.get_by_codigo(dto.codigo_medidor)
            if medidor_existente:
                raise BusinessRuleException(f"El medidor con código '{dto.codigo_medidor}' ya está registrado.")

        # 4. Crear y Persistir Terreno
        nuevo_terreno = Terreno(
            id=None,
            socio_id=dto.socio_id,
            barrio_id=dto.barrio_id,
            direccion=dto.direccion,
            es_cometida_activa=True
        )

        terreno_creado = self.terreno_repo.create(nuevo_terreno)

        # 5. LÓGICA AUTOMÁTICA DE SERVICIOS (Tesis) ####
        if dto.tiene_medidor:
            # CASO A: Crear Medidor
            nuevo_medidor = Medidor(
                id=None,
                terreno_id=terreno_creado.id,
                codigo=dto.codigo_medidor,
                marca=dto.marca_medidor,
                lectura_inicial=dto.lectura_inicial if dto.lectura_inicial else 0.0,
                estado='ACTIVO',
                observacion=dto.observacion
            )
            self.medidor_repo.create(nuevo_medidor)

            # Opcional: Crear servicio tipo 'VARIABLE'
            self.servicio_repo.create_automatico(
                terreno_id=terreno_creado.id,
                socio_id=terreno_creado.socio_id, # Requerido por el Repositorio
                tipo='VARIABLE',
                valor=3.00 # Tarifa base según Reglamento Art. 5
            )
        else:
            # #### CASO B: Es Acometida (Tarifa Fija)
            # El sistema crea automáticamente el servicio usando la constante del DOMINIO
            self.servicio_repo.create_automatico(
                terreno_id=terreno_creado.id,
                socio_id=terreno_creado.socio_id,
                tipo='FIJO',
                valor=TARIFA_FIJA_SIN_MEDIDOR  # ✅ Aquí se aplican los $5.00 automáticamente
            )

        return terreno_creado