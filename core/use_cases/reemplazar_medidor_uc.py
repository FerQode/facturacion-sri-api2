# core/use_cases/reemplazar_medidor_uc.py
from django.db import transaction # Ojo: Idealmente abstraer esto, pero por practicidad lo usamos aquí
from core.interfaces.repositories import IMedidorRepository, ILecturaRepository
from core.domain.medidor import Medidor
from core.domain.lectura import Lectura # Asumiendo que tienes esta entidad
from core.use_cases.medidor_dtos import ReemplazarMedidorDTO
from core.shared.exceptions import EntityNotFoundException, BusinessRuleException
from datetime import date

class ReemplazarMedidorUseCase:
    def __init__(self, medidor_repo: IMedidorRepository, lectura_repo: ILecturaRepository):
        self.medidor_repo = medidor_repo
        self.lectura_repo = lectura_repo

    def ejecutar(self, dto: ReemplazarMedidorDTO):
        # Usamos transacción para que si algo falla, no quede nada a medias
        # (Nota: En clean architecture puro, la transacción suele manejarse en el adaptador, 
        # pero para lógica compleja entre repos, es aceptable aquí o en un UnitOfWork).
        
        # 1. Buscar el medidor ACTUAL instalado en el terreno
        medidor_viejo = self.medidor_repo.get_by_terreno_id(dto.terreno_id)
        if not medidor_viejo:
            raise EntityNotFoundException("El terreno no tiene un medidor activo para reemplazar.")

        # 2. Validar Lógica: La lectura final no puede ser menor a la inicial
        if dto.lectura_final_viejo < medidor_viejo.lectura_inicial:
            raise BusinessRuleException("La lectura final no puede ser menor a la lectura inicial del medidor viejo.")

        # --- APLICANDO RECOMENDACIÓN #2: LA TRAMPA DE FACTURACIÓN ---
        # Registramos la última lectura del medidor viejo para que Facturación
        # pueda calcular el consumo hasta hoy.
        ultima_lectura = Lectura(
            id=None,
            medidor_id=medidor_viejo.id,
            valor=dto.lectura_final_viejo,
            fecha=date.today(),
            observacion=f"Lectura final por retiro. Motivo: {dto.motivo_cambio}"
            # usuario_id=dto.usuario_id (Si tu entidad Lectura soporta auditoría)
        )
        self.lectura_repo.save(ultima_lectura)

        # --- APLICANDO RECOMENDACIÓN #1: SOFT DELETE / HISTORIAL ---
        # 3. "Jubilar" al medidor viejo
        medidor_viejo.terreno_id = None  # Desvincular del terreno
        medidor_viejo.estado = dto.motivo_cambio # 'DANADO', 'ROBADO'
        medidor_viejo.observacion = f"Reemplazado el {date.today()}. Lectura final: {dto.lectura_final_viejo}"
        self.medidor_repo.save(medidor_viejo)

        # 4. Instalar Medidor Nuevo
        nuevo_medidor = Medidor(
            id=None,
            terreno_id=dto.terreno_id, # Toma el lugar del viejo
            codigo=dto.codigo_nuevo,
            marca=dto.marca_nueva,
            lectura_inicial=dto.lectura_inicial_nuevo,
            estado='ACTIVO',
            observacion=f"Instalado por cambio. Usuario: {dto.usuario_id}"
        )
        self.medidor_repo.create(nuevo_medidor)

        return nuevo_medidor