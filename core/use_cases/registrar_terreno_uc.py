from typing import Optional

# Importamos las Interfaces (Contratos)
from core.interfaces.repositories import (
    ITerrenoRepository, 
    IMedidorRepository, 
    ISocioRepository, 
    IBarrioRepository
)

# Importamos las Entidades de Dominio
from core.domain.terreno import Terreno
from core.domain.medidor import Medidor

# Importamos el DTO
from core.use_cases.terreno_dtos import RegistrarTerrenoDTO

# Importamos excepciones personalizadas (ajusta según tu archivo shared/exceptions.py)
# Si no las tienes creadas aún, puedes usar Exception temporalmente o crearlas en core/shared/exceptions.py
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

class RegistrarTerrenoUseCase:
    def __init__(self, 
                 terreno_repo: ITerrenoRepository, 
                 medidor_repo: IMedidorRepository,
                 socio_repo: ISocioRepository,
                 barrio_repo: IBarrioRepository):
        # Inyección de Dependencias: No dependemos de Django, sino de las interfaces
        self.terreno_repo = terreno_repo
        self.medidor_repo = medidor_repo
        self.socio_repo = socio_repo
        self.barrio_repo = barrio_repo

    def ejecutar(self, dto: RegistrarTerrenoDTO) -> Terreno:
        """
        Orquesta el registro de un terreno y su medidor opcional.
        Sigue el principio de 'Todo o Nada' (Integridad Transaccional lógica).
        """
        
        # 1. Validar que el Socio existe
        if not self.socio_repo.get_by_id(dto.socio_id):
            raise EntityNotFoundException(f"El socio con ID {dto.socio_id} no existe.")

        # 2. Validar que el Barrio existe (Ubicación física)
        if not self.barrio_repo.get_by_id(dto.barrio_id):
            raise EntityNotFoundException(f"El barrio con ID {dto.barrio_id} no existe.")

        # 3. Validaciones de Negocio para el Medidor (si aplica)
        if dto.tiene_medidor:
            if not dto.codigo_medidor:
                raise BusinessRuleException("Si el terreno tiene medidor, el código es obligatorio.")
            
            # Verificar que el código no esté duplicado en el sistema
            medidor_existente = self.medidor_repo.get_by_codigo(dto.codigo_medidor)
            if medidor_existente:
                raise BusinessRuleException(f"El medidor con código '{dto.codigo_medidor}' ya está registrado en el sistema.")

        # 4. Crear la Entidad Terreno (Objeto puro, sin ID aún)
        nuevo_terreno = Terreno(
            id=None,
            socio_id=dto.socio_id,
            barrio_id=dto.barrio_id,
            direccion=dto.direccion,
            es_cometida_activa=True
        )
        
        # 5. Persistir Terreno (Aquí el Repositorio le asigna un ID y lo guarda)
        terreno_creado = self.terreno_repo.create(nuevo_terreno)

        # 6. Crear y Persistir Medidor (Solo si el usuario dijo que tenía)
        if dto.tiene_medidor:
            nuevo_medidor = Medidor(
                id=None,
                terreno_id=terreno_creado.id, # <--- ¡CONEXIÓN CRÍTICA! Vinculamos al ID recién creado
                codigo=dto.codigo_medidor,
                marca=dto.marca_medidor,
                lectura_inicial=dto.lectura_inicial if dto.lectura_inicial else 0.0,
                estado='ACTIVO',
                observacion=dto.observacion
            )
            self.medidor_repo.create(nuevo_medidor)

        return terreno_creado