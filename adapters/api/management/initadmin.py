# adapters/api/management/commands/initadmin.py
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Crea un superusuario automáticamente si no existe"

    def handle(self, *args, **options):
        # Leemos variables de entorno (o defaults seguros)
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@juntaarbolito.com')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        if not User.objects.filter(username=username).exists():
            print(f"👤 Creando superusuario '{username}'...")
            User.objects.create_superuser(username, email, password)
            print("✅ Superusuario creado exitosamente.")
        else:
            print(f"ℹ️ El superusuario '{username}' ya existe.")
