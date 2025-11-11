from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adapters.api' # <--- ESTA ES LA SOLUCIÓN
