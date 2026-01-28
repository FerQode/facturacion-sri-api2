# config/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el módulo de configuración de Django por defecto para el programa 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Usar una cadena aquí significa que el trabajador no tiene que serializar
# el objeto de configuración a los procesos hijos.
# - namespace='CELERY' significa que todas las claves de configuración
#   celery deben tener el prefijo 'CELERY_'.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carga módulos de tareas de todas las aplicaciones de la aplicación Django registradas.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
