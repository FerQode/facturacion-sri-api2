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
        # Lista de Cédulas Válidas (Generadas para pruebas, cumplen algoritmo Mod10)
        valid_cedulas = [
            "1710034065", 
            "1722246392", 
            "0910000005", 
            "0915437172", 
            "1102945415"
        ]

        socios = []
        for i, val_id in enumerate(valid_cedulas, 1):
            cedula = val_id
            user_socio, _ = User.objects.get_or_create(username=cedula)
            # Estrategia Dev: Clave = Identificación
            user_socio.set_password(cedula)
            user_socio.save()
            
            socio, _ = SocioModel.objects.get_or_create(
                identificacion=cedula,
                defaults={
                    'nombres': f"Socio_{i}", 'apellidos': "Test",
                    'usuario': user_socio, 'barrio': barrio, 'direccion': f"Calle {i}",
                    'tipo_identificacion': 'C' 
                }
            )
            socios.append(socio)
        self.stdout.write("5 Socios creados.")

        # 3.1 Socio RUC (Hacienda La Esperanza)
        ruc = "1790011674001" # RUC Válido
        user_ruc, _ = User.objects.get_or_create(username=ruc)
        user_ruc.set_password(ruc)
        user_ruc.save()
        
        socio_ruc, _ = SocioModel.objects.get_or_create(
            identificacion=ruc,
            defaults={
                'nombres': "Hacienda La Esperanza", 'apellidos': "(Empresa)",
                'usuario': user_ruc, 'barrio': barrio, 'direccion': "Via a la Costa Km 10",
                'tipo_identificacion': 'R'
            }
        )
        self.stdout.write("Socio RUC creado (Hacienda La Esperanza).")

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
