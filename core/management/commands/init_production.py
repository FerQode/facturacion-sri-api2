# core/management/commands/init_production.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.db import transaction

class Command(BaseCommand):
    help = 'Inicializa los datos de Producción (Usuarios y Roles)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando carga de datos de Producción...'))

        datos_usuarios = [
            {
                'username': 'el.arbolito25ad@gmail.com',
                'password': 'Admin123;',
                'first_name': 'FERNANDO ROMEL',
                'last_name': 'QUINAPALLO QUINAPALLO',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'el.arbolito2tes@gmail.com',
                'password': 'Tesorero133;',
                'first_name': 'Mayury Jhomayra',
                'last_name': 'Plasencia Velasco',
                'role': 'TESORERO',
                'is_staff': True,
                'is_superuser': False
            },
            {
                'username': 'elarbolitooperador@gmail.com',
                'password': 'Operador123;',
                'first_name': 'Edison Geovanny',
                'last_name': 'Unaucho Choloquinga',
                'role': 'OPERADOR',
                'is_staff': True,
                'is_superuser': False
            },
            {
                'username': 'secretarioelarbolito@gmail.com',
                'password': 'Secretario123;',
                'first_name': 'Alexis Ismael',
                'last_name': 'Vega Toroche',
                'role': 'SECRETARIO',
                'is_staff': True,
                'is_superuser': False
            }
        ]

        with transaction.atomic():
            # 1. Crear Grupos
            grupos = ['ADMIN', 'TESORERO', 'OPERADOR', 'SECRETARIO']
            for nombre_grupo in grupos:
                group, created = Group.objects.get_or_create(name=nombre_grupo)
                if created:
                    self.stdout.write(f'Grupo creado: {nombre_grupo}')
                else:
                    self.stdout.write(f'Grupo existente: {nombre_grupo}')

            # 2. Crear Usuarios
            for data in datos_usuarios:
                user, created = User.objects.get_or_create(
                    username=data['username'],
                    defaults={
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                        'email': data['username'],
                        'is_staff': data['is_staff'],
                        'is_superuser': data['is_superuser']
                    }
                )

                if created:
                    user.set_password(data['password'])
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Usuario creado: {data["username"]}'))
                else:
                    # Actualizar password si ya existe (Opcional, pero útil para reset)
                    user.set_password(data['password'])
                    user.first_name = data['first_name']
                    user.last_name = data['last_name']
                    user.is_staff = data['is_staff']
                    user.is_superuser = data['is_superuser']
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Usuario actualizado: {data["username"]}'))

                # Asignar Grupo
                group = Group.objects.get(name=data['role'])
                user.groups.add(group)
                self.stdout.write(f' -> Asignado a grupo: {data["role"]}')

        self.stdout.write(self.style.SUCCESS('✅ Carga de Producción COMPLETADA'))
