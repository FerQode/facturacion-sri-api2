# adapters/infrastructure/repositories/django_socio_repository.py
from typing import List, Optional
from core.domain.socio import Socio
from core.interfaces.repositories import ISocioRepository
from adapters.infrastructure.models import SocioModel

# Manejo robusto de Enums para evitar errores de importación
try:
    from core.shared.enums import RolUsuario
except ImportError:
    RolUsuario = None

class DjangoSocioRepository(ISocioRepository):
    """
    Implementación del repositorio de Socios usando el ORM de Django.
    Cumple estrictamente con el contrato de ISocioRepository.
    """

    # =================================================================
    # 1. TRADUCTOR (ORM -> DOMINIO)
    # =================================================================
    def _map_model_to_domain(self, model: SocioModel) -> Socio:
        """
        Convierte un SocioModel (Django) a Socio (Dominio).
        """
        # Lógica defensiva para el Rol
        rol_valor = "SOCIO"
        if hasattr(model, 'rol') and model.rol:
            rol_valor = model.rol
            if RolUsuario:
                try:
                    rol_valor = RolUsuario(model.rol)
                except ValueError:
                    pass

        return Socio(
            id=model.id,
            identificacion=model.identificacion,
            tipo_identificacion=model.tipo_identificacion,
            nombres=model.nombres,
            apellidos=model.apellidos,
            email=model.email,
            telefono=model.telefono,
            barrio_id=model.barrio_id,
            direccion=model.direccion,
            esta_activo=getattr(model, 'esta_activo', True),
            rol=rol_valor,
            # Mapeo seguro del usuario de sistema
            usuario_id=model.usuario_id if hasattr(model, 'usuario') and model.usuario else None,
            _validate=False  # Hidratación segura para lecturas
        )

    # =================================================================
    # 2. IMPLEMENTACIÓN DE LA INTERFAZ (LECTURA)
    # =================================================================
    def get_by_id(self, socio_id: int) -> Optional[Socio]:
        try:
            # select_related optimiza trayendo la relación 'usuario' en una sola query
            model = SocioModel.objects.select_related('usuario').get(pk=socio_id)
            return self._map_model_to_domain(model)
        except SocioModel.DoesNotExist:
            return None

    def get_by_identificacion(self, identificacion: str) -> Optional[Socio]:
        try:
            model = SocioModel.objects.select_related('usuario').get(identificacion=identificacion)
            return self._map_model_to_domain(model)
        except SocioModel.DoesNotExist:
            return None

    # ✅ ESTE ES EL MÉTODO QUE FALTABA Y CAUSABA EL ERROR DE ARRANQUE
    def get_by_usuario_id(self, usuario_id: int) -> Optional[Socio]:
        """
        Busca un socio basándose en su ID de usuario de sistema (Login).
        Requerido por ISocioRepository.
        """
        try:
            model = SocioModel.objects.select_related('usuario').get(usuario_id=usuario_id)
            return self._map_model_to_domain(model)
        except SocioModel.DoesNotExist:
            return None

    def list_all(self) -> List[Socio]:
        qs = SocioModel.objects.select_related('usuario').all().order_by('apellidos')
        return [self._map_model_to_domain(m) for m in qs]

    def list_active(self) -> List[Socio]:
        qs = SocioModel.objects.select_related('usuario').filter(esta_activo=True).order_by('apellidos')
        return [self._map_model_to_domain(m) for m in qs]

    def list_by_barrio(self, barrio_id: int) -> List[Socio]:
        qs = SocioModel.objects.select_related('usuario').filter(esta_activo=True, barrio_id=barrio_id).order_by('apellidos')
        return [self._map_model_to_domain(m) for m in qs]

    # =================================================================
    # 3. IMPLEMENTACIÓN DE LA INTERFAZ (ESCRITURA)
    # =================================================================
    def create(self, socio: Socio) -> Socio:
        """Alias para cumplir con interfaces que pidan create explícito"""
        return self.save(socio)

    def save(self, socio: Socio) -> Socio:
        # Preparamos los datos
        data_db = {
            'identificacion': socio.identificacion,
            'tipo_identificacion': socio.tipo_identificacion,
            'nombres': socio.nombres,
            'apellidos': socio.apellidos,
            'email': socio.email,
            'telefono': socio.telefono,
            'barrio_id': socio.barrio_id,
            'direccion': socio.direccion,
            'esta_activo': socio.esta_activo,
            'usuario_id': socio.usuario_id
        }
        
        # Convertimos el Enum a string para la BD
        if hasattr(socio, 'rol') and socio.rol:
            val = socio.rol.value if hasattr(socio.rol, 'value') else str(socio.rol)
            data_db['rol'] = val

        # Lógica segura de guardado
        if socio.id:
            # Update
            SocioModel.objects.filter(pk=socio.id).update(**data_db)
            # Recargamos para devolver el objeto fresco
            model = SocioModel.objects.get(pk=socio.id)
        else:
            # Create
            model = SocioModel.objects.create(**data_db)
            socio.id = model.id
            
        return self._map_model_to_domain(model)