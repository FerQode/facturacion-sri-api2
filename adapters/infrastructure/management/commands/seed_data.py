# adapters.infrastructure.management.commands.seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from adapters.infrastructure.models import (
    SocioModel, BarrioModel, TerrenoModel, ServicioModel, MedidorModel, LecturaModel
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Poblar base de datos con escenario de prueba para Periodos Fiscales'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Iniciando Seed Data ---")
        
        # 1. Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
            self.stdout.write("Admin creado.")

        # 2. Barrio
        barrio, _ = BarrioModel.objects.get_or_create(nombre="Barrio Central")

        # 3. Socios (5)
        socios = []
        for i in range(1, 6):
            cedula = f"110000000{i}"
            user_socio, _ = User.objects.get_or_create(username=cedula)
            user_socio.set_password("1234")
            user_socio.save()
            
            socio, _ = SocioModel.objects.get_or_create(
                cedula=cedula,
                defaults={
                    'nombres': f"Socio_{i}", 'apellidos': "Test",
                    'usuario': user_socio, 'barrio': barrio, 'direccion': f"Calle {i}"
                }
            )
            socios.append(socio)
        self.stdout.write("5 Socios creados.")

        # 4. Servicios Fijos (2) - Socios 1 y 2
        for i in range(2):
            terreno, _ = TerrenoModel.objects.get_or_create(
                direccion=f"Lote Fijo {i}", barrio=barrio, socio=socios[i]
            )
            ServicioModel.objects.get_or_create(
                socio=socios[i], terreno=terreno, 
                defaults={'tipo': 'FIJO', 'activo': True}
            )
        self.stdout.write("2 Servicios Fijos creados.")

        # 5. Medidores Activos (3) - Socios 3, 4, 5
        for i in range(2, 5):
            terreno, _ = TerrenoModel.objects.get_or_create(
                direccion=f"Lote Medido {i}", barrio=barrio, socio=socios[i]
            )
            # Servicio Medido
            srv, _ = ServicioModel.objects.get_or_create(
                socio=socios[i], terreno=terreno,
                defaults={'tipo': 'MEDIDO', 'activo': True}
            )
            
            # Medidor
            medidor, _ = MedidorModel.objects.get_or_create(
                codigo=f"MED-00{i}",
                defaults={'marca': 'Zenner', 'estado': 'ACTIVO', 'terreno': terreno}
            )
            
            # LECTURAS HISTORICAS (Octubre y Noviembre 2025)
            # Octubre
            LecturaModel.objects.get_or_create(
                medidor=medidor, anio=2025, mes=10,
                defaults={
                    'valor': 100 + (i*10), 
                    'fecha': date(2025, 10, 15),
                    'lectura_anterior': 0,
                    'consumo_del_mes': 0
                }
            )
            # Noviembre
            LecturaModel.objects.get_or_create(
                medidor=medidor, anio=2025, mes=11,
                defaults={
                    'valor': 120 + (i*10), 
                    'fecha': date(2025, 11, 15),
                    'lectura_anterior': 100 + (i*10),
                    'consumo_del_mes': 20
                }
            )
            
        self.stdout.write("3 Medidores y Lecturas Históricas (Oct/Nov/2025) creadas.")
        self.stdout.write(self.style.SUCCESS("--- SEED DATA COMPLETADO ---"))
