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
    help = 'Poblar base de datos con Datos Reales de la Junta de Agua'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Iniciando Carga de Datos Reales ---")

        # 1. Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@admin.com', 'admin')
            self.stdout.write("Admin creado (admin/admin).")

        # 1.5. CREAR RUBROS BASE
        self.stdout.write("--- Creando Rubros Base ---")
        from adapters.infrastructure.models import CatalogoRubroModel

        rubros_base = [
            {"nombre": "TARIFA_AGUA_POTABLE", "tipo": "AGUA_POTABLE", "valor": 3.00, "iva": False},
            {"nombre": "TARIFA_ALCANTARILLADO", "tipo": "ALCANTARILLADO", "valor": 1.50, "iva": False},
            {"nombre": "MULTA_REUNION", "tipo": "MULTA", "valor": 5.00, "iva": False},
            {"nombre": "MULTA_MINGA", "tipo": "MULTA", "valor": 10.00, "iva": False},
            {"nombre": "DERECHO_ACOMETIDA", "tipo": "OTROS", "valor": 150.00, "iva": False},
            {"nombre": "AUDITORIA_V5", "tipo": "OTROS", "valor": 0.00, "iva": True},
        ]
        
        for r in rubros_base:
            CatalogoRubroModel.objects.get_or_create(
                nombre=r['nombre'],
                defaults={
                    'tipo': r['tipo'],
                    'valor_unitario': r['valor'],
                    'iva': r['iva'],
                    'activo': True
                }
            )
        self.stdout.write("Rubros base creados.")

        # DATOS REALES
        datos_reales = [
            {"cedula": "0501900369", "nombre_completo": "ACHOTE PALOMO ANGEL", "direccion": "Vascones", "email": "achotepalomo@test.com", "telefono": ""},
            {"cedula": "0502389943", "nombre_completo": "ACURIO ACURIO ABRAHAM", "direccion": "La Loma", "telefono": "0959106060", "email": "abac_amigo@test.com"},
            {"cedula": "17525854950", "nombre_completo": "ACURIO ACURIO ADRIAN", "direccion": "Isinche de alpamalag", "telefono": "0998387298", "email": "mariselaacuri@test.com"},
            {"cedula": "0500750195", "nombre_completo": "ACURIO ACURIO ANA BEATRIZ", "direccion": "La Loma", "telefono": "0997810534", "email": "ana.beatriz20@test.com"},
            {"cedula": "1701587394", "nombre_completo": "ACURIO ACURIO ANGEL FABIAN", "direccion": "La Loma", "telefono": "0959106060", "email": "abac_amigo@test.com"},
            {"cedula": "0500636998", "nombre_completo": "ACURIO ACURIO EVA PIEDAD", "direccion": "La Loma", "telefono": "0995524753", "email": "acuriodanilo@test.com"},
            {"cedula": "0500650858", "nombre_completo": "ACURIO ACURIO GLORIA", "direccion": "La Loma", "telefono": "", "email": ""},
            {"cedula": "0502438401", "nombre_completo": "ACURIO ACURIO LUIS GERMAN", "direccion": "La Loma", "telefono": "0993631903", "email": "luis_ga2@test.com"},
            {"cedula": "1702446723", "nombre_completo": "ACURIO ACURIO MANUEL", "direccion": "La Loma", "telefono": "0999331180", "email": ""},
            {"cedula": "0500542840", "nombre_completo": "ACURIO ACURIO MARIA CLEMENCIA", "direccion": "Isinche de Alpamalag", "telefono": "0999097512", "email": "guatusin70@test.com"}
        ]

        count = 0
        for info in datos_reales:
            cedula = info['cedula']
            nombre_completo = info['nombre_completo']
            direccion_raw = info.get('direccion', '').strip()
            email = info.get('email', '')
            telefono = info.get('telefono', '')

            # 2. Lógica de Barrio Dinámica
            nombre_barrio = direccion_raw if direccion_raw else "Barrio General"
            barrio, _ = BarrioModel.objects.get_or_create(nombre=nombre_barrio)
            
            # Formato de Nombres (2 apellidos, resto nombres) - Ajuste básico
            parts = nombre_completo.split()
            if len(parts) >= 2:
                apellidos = " ".join(parts[:2])
                nombres = " ".join(parts[2:])
            else:
                apellidos = nombre_completo
                nombres = ""

            # 3. y 4. Crear Usuario y Socio
            # (Simplificado: Sin User asociado si no es necesario para login)
            user_socio, created = User.objects.get_or_create(username=cedula)
            if created:
                user_socio.set_password(cedula)
                user_socio.save()

            socio, created_socio = SocioModel.objects.get_or_create(
                identificacion=cedula,
                defaults={
                    'nombres': nombres, 
                    'apellidos': apellidos,
                    'usuario': user_socio, 
                    'barrio': barrio, 
                    'direccion': direccion_raw,
                    'tipo_identificacion': 'C', # Default a Cédula
                    'email': email,
                    'telefono': telefono,
                    'modalidad_cobro': 'FIJO' # Default para datos semilla
                }
            )

            # 5. Crear Terreno y Servicio (si es nuevo socio)
            if created_socio:
                terreno, _ = TerrenoModel.objects.get_or_create(
                    direccion=f"Casa de {nombres}", 
                    barrio=barrio, 
                    socio=socio
                )
                
                ServicioModel.objects.get_or_create(
                    socio=socio, 
                    terreno=terreno, 
                    defaults={'tipo': 'AGUA_POTABLE', 'estado': 'ACTIVO', 'valor_tarifa': 3.00}
                )
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f"--- SEED DATA COMPLETADO: {count} nuevos socios reales insertados ---"))
