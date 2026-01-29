# config/__init__.py
from __future__ import absolute_import, unicode_literals

# Esto asegurará que la app de Celery se cargue siempre que
# Django arranque, para que @shared_task funcione.

from .celery import app as celery_app

__all__ = ('celery_app',)
