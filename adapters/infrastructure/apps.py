# adapters/infrastructure/apps.py
from django.apps import AppConfig

class InfrastructureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adapters.infrastructure'
    verbose_name = 'Infraestructura y Datos'

    def ready(self):
        """
        Método de arranque de la aplicación.
        Aquí importamos los Signals para asegurar que se registren 
        cuando Django inicia.
        """
        try:
            import adapters.infrastructure.signals
        except ImportError:
            # Si no existe el archivo signals.py aún, no rompemos la app
            pass
