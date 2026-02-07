# adapters>infrastructure>apps.py
from django.apps import AppConfig

class InfrastructureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adapters.infrastructure'
    verbose_name = 'Infraestructura y Datos'
