# adapters/infrastructure/repositories/django_medidor_repository.py

from typing import List, Optional
from core.interfaces.repositories import IMedidorRepository
from core.domain.medidor import Medidor
from adapters.infrastructure.models import MedidorModel

class DjangoMedidorRepository(IMedidorRepository):
    """
    Implementación del Repositorio de Medidores usando el ORM de Django.
    """

    def _to_entity(self, model: MedidorModel) -> Medidor:
        """
        Mapeador: Modelo de Django -> Entidad de Dominio
        CORRECCIÓN CRÍTICA: Usamos model.socio_id para evitar errores
        si la relación de socio no se carga correctamente o no existe.
        """
        return Medidor(
            id=model.id,
            codigo=model.codigo,
            socio_id=model.socio_id, # <--- CLAVE: Acceso directo al ID foráneo
            esta_activo=model.esta_activo,
            observacion=model.observacion,
            tiene_medidor_fisico=model.tiene_medidor_fisico
        )

    def get_by_id(self, medidor_id: int) -> Optional[Medidor]:
        """Obtiene un medidor por su ID."""
        try:
            model = MedidorModel.objects.get(pk=medidor_id)
            return self._to_entity(model)
        except MedidorModel.DoesNotExist:
            return None

    def list_by_socio(self, socio_id: int) -> List[Medidor]:
        """Lista todos los medidores de un socio específico."""
        models = MedidorModel.objects.filter(socio_id=socio_id)
        return [self._to_entity(m) for m in models]

    # --- MÉTODOS REQUERIDOS POR LOS CASOS DE USO ---

    def list_all(self) -> List[Medidor]:
        """Lista TODOS los medidores del sistema."""
        models = MedidorModel.objects.all()
        return [self._to_entity(m) for m in models]

    def get_by_codigo(self, codigo: str) -> Optional[Medidor]:
        """
        Busca un medidor por su código único.
        Útil para validaciones antes de crear uno nuevo.
        """
        try:
            model = MedidorModel.objects.get(codigo=codigo)
            return self._to_entity(model)
        except MedidorModel.DoesNotExist:
            return None
    
    def save(self, medidor: Medidor) -> Medidor:
        """Guarda o actualiza un medidor en la base de datos."""
        if medidor.id:
            # Actualizar existente
            try:
                model = MedidorModel.objects.get(pk=medidor.id)
                model.codigo = medidor.codigo
                model.socio_id = medidor.socio_id
                model.esta_activo = medidor.esta_activo
                model.observacion = medidor.observacion
                model.tiene_medidor_fisico = medidor.tiene_medidor_fisico
            except MedidorModel.DoesNotExist:
                 # Fallback por seguridad, aunque no debería pasar si el ID viene de la entidad
                 return self.save(medidor) # Intentar crear si no existe
        else:
            # Crear nuevo
            model = MedidorModel(
                codigo=medidor.codigo,
                socio_id=medidor.socio_id,
                esta_activo=medidor.esta_activo,
                observacion=medidor.observacion,
                tiene_medidor_fisico=medidor.tiene_medidor_fisico
            )
        
        model.save()
        medidor.id = model.id # Devolvemos la entidad con el ID asignado por la BBDD
        return medidor