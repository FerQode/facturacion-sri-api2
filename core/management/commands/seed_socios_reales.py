from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User, Group
from adapters.infrastructure.models import (
    SocioModel, BarrioModel, MedidorModel, ServicioModel, TerrenoModel
)
from datetime import datetime, date

class Command(BaseCommand):
    help = 'Carga inicial de Socios Reales con sanitización y normalización de datos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('🌱 INICIANDO CARGA DE SOCIOS REALES...'))
        
        # --- 1. CONFIGURACIÓN DATA RAW ---
        data_raw = [
            {"cedula": "0501900369", "nombre_completo": "ACHOTE PALOMO ANGEL RODRIGO", "barrio_raw": "Vascones", "email": "achotepalomoa@gmail.com", "telefono": "0999999999"},
            {"cedula": "0502389943", "nombre_completo": "ACURIO ACURIO ABRAHAM AQUILINO", "barrio_raw": "La Loma", "email": "abac_amigo@hotmail.com", "telefono": "0959106060"},
            {"cedula": "1752585495001", "nombre_completo": "ACURIO ACURIO ADRIAN MAURICIO", "barrio_raw": "Isinche de alpamalag", "email": "mariselaacurio85@gmail.com", "telefono": "0998387298"},
            {"cedula": "0500750195", "nombre_completo": "ACURIO ACURIO ANA BEATRIZ", "barrio_raw": "La Loma", "email": "ana.beatriz2020@outlook.es", "telefono": "0997810534"},
            {"cedula": "1701587394", "nombre_completo": "ACURIO ACURIO ANGEL FRANCISCO", "barrio_raw": "La Loma", "email": "abac_amigo@hotmail.com", "telefono": "0959106060"}, # OJO: Email repetido con el ID 3
            {"cedula": "0500636998", "nombre_completo": "ACURIO ACURIO EVA PIEDAD", "barrio_raw": "La Loma", "email": "acuriodanilo@gmail.com", "telefono": "0995524753"},
            {"cedula": "0502438401", "nombre_completo": "ACURIO ACURIO LUIS GERARDO", "barrio_raw": "La Loma", "email": "luis_ga2@hotmail.com", "telefono": "0993631903"},
            {"cedula": "0500542840", "nombre_completo": "ACURIO ACURIO MARIA CLEOTILDE ASUNCION", "barrio_raw": "Isinche de Alpamalag", "email": "guatusin70@hotmail.com", "telefono": "0999097512"},
            {"cedula": "0501490528", "nombre_completo": "ACURIO ACURIO MARIA TERESA", "barrio_raw": "La Loma", "email": "teresaacurio93@gmail.com", "telefono": ""},
            {"cedula": "0501499750", "nombre_completo": "ACURIO ACURIO MARIANA PIEDAD", "barrio_raw": "La Loma", "email": "maryacurio@live.com", "telefono": ""},
            {"cedula": "0502455983", "nombre_completo": "ACURIO ACURIO WALTER EFREN", "barrio_raw": "Isinche de Alpamalag", "email": "acuriodarwin1982@gmail.com", "telefono": "0984728747"},
            {"cedula": "0502160765", "nombre_completo": "ACURIO MOLINA NORMA JAQUELINE", "barrio_raw": "La Loma", "email": "jaap2022aguaal@gmail.com", "telefono": "0958793320"},
            {"cedula": "0500615976", "nombre_completo": "ACURIO PAREDES MARIA LUZMILA", "barrio_raw": "San Agustin", "email": "luzmilaacurio53@hotmail.com", "telefono": "0992892970"},
            {"cedula": "1707028286", "nombre_completo": "ALLAUCA CRIOLLO VIRGILIO RUBEN", "barrio_raw": "Vasconez", "email": "allaucaruben@gmail.com", "telefono": ""},
            {"cedula": "0503121402", "nombre_completo": "BASANTE ACURIO NELSON GERARDO", "barrio_raw": "San Agustin", "email": "nelgerbasante@gmail.com", "telefono": "0992892970"},
            {"cedula": "0501680565", "nombre_completo": "BELAÑO PALOMO MARIA ANTONIETA", "barrio_raw": "Maldonados", "email": "mariabelano7@gmail.com", "telefono": ""},
            {"cedula": "0502582588", "nombre_completo": "CAIZA GUANOTASIG EDGAR VICENTE", "barrio_raw": "Isinche de Alpamalag", "email": "vicentecaisa12@hotmail.com", "telefono": "0995317128"},
            {"cedula": "0500969316", "nombre_completo": "CAIZA GUANOTASIG LUZ MARIA", "barrio_raw": "Isinche de Alpamalag", "email": "vicentecaiza12@gmail.com", "telefono": "0995317128"},
            {"cedula": "171370932", "nombre_completo": "CATOTA CHASI MARIA OLGA", "barrio_raw": "Alpamalag de Isinche", "email": "", "telefono": "0994341995"}, # ERROR INTENCIONAL
            {"cedula": "1803291408", "nombre_completo": "PAREDES ACURIO CARLOS HERIBERTO", "barrio_raw": "La Loma", "email": "heriparedesacurio@gmail.com", "telefono": ""}
        ]

        # --- 2. DICCIONARIO NORMALIZACIÓN BARRIOS ---
        # Key: Lo que viene en el Excel (lower case for robust matching)
        # Value: El nombre correcto en DB
        barrio_map = {
            "vascones": "Vásconez",
            "vasconez": "Vásconez",
            "san agustin": "San Agustín",
            "la loma": "La Loma",
            "isinche de alpamalag": "Isinche de Alpamalag",
            "alpamalag de isinche": "Isinche de Alpamalag", # Asumiendo normalización
            "maldonados": "Maldonados"
        }

        # --- 3. PROCESAMIENTO ---
        created_count = 0
        errors = []

        # Asegurar Barrio Default
        default_barrio, _ = BarrioModel.objects.get_or_create(nombre="Sin Asignar")

        # Asegurar Grupo Socio
        grupo_socio, _ = Group.objects.get_or_create(name="Socio")

        for item in data_raw:
            cedula = item['cedula'].strip()
            nombre_completo = item['nombre_completo'].strip().upper()
            barrio_raw = item['barrio_raw'].strip()
            email_raw = item['email'].strip().lower()

            try:
                with transaction.atomic():
                    # A. VALIDACIÓN CÉDULA
                    if not cedula.isdigit() or len(cedula) not in [10, 13]:
                        raise ValueError(f"Longitud o formato inválido ({len(cedula)} dígitos)")

                    # B. NORMALIZACIÓN BARRIO
                    nombre_barrio_correcto = barrio_map.get(barrio_raw.lower(), default_barrio.nombre)
                    barrio, _ = BarrioModel.objects.get_or_create(nombre=nombre_barrio_correcto)

                    # C. SPLIT NOMBRES
                    palabras = nombre_completo.split()
                    if len(palabras) >= 3:
                        apellidos = f"{palabras[0]} {palabras[1]}"
                        nombres = " ".join(palabras[2:])
                    elif len(palabras) == 2:
                        apellidos = palabras[0]
                        nombres = palabras[1]
                    else:
                        apellidos = nombre_completo
                        nombres = "."

                    # D. GESTIÓN USUARIO (Manejo de Duplicados)
                    username = cedula
                    email_final = email_raw
                    
                    # Si el email está vacío o ya existe en otro usuario, generar dummy
                    if not email_final or User.objects.filter(email=email_final).exclude(username=username).exists():
                        email_final = f"{cedula}@bancoarbolito.com"
                        self.stdout.write(self.style.WARNING(f"   ⚠️ Email ajustado para {cedula}: {email_final}"))

                    user, created_user = User.objects.get_or_create(username=username)
                    if created_user:
                        user.email = email_final
                        user.set_password(f"Arbolito.{cedula}") # Password default segura
                        user.first_name = nombres[:30]
                        user.last_name = apellidos[:30]
                        user.save()
                        user.groups.add(grupo_socio)

                    # E. CREACIÓN SOCIO
                    socio, created_socio = SocioModel.objects.get_or_create(
                        identificacion=cedula,
                        defaults={
                            "usuario": user,
                            "nombres": nombres,
                            "apellidos": apellidos,
                            "email": email_final,
                            "telefono": item['telefono'],
                            "barrio": barrio,
                            "direccion": f"Casa en {barrio.nombre}", # Default
                            "fecha_nacimiento": date(2000, 1, 1) # Default date
                        }
                    )
                    
                    if not created_socio:
                        # Update fields if exists
                        socio.nombres = nombres
                        socio.apellidos = apellidos
                        socio.barrio = barrio
                        socio.save()

                    # F. BOOTSTRAPPING SERVICIOS (Medidor + Agua)
                    # Solo si no tiene servicios activos
                    if not socio.servicios.exists():
                        # Crear Terreno Default
                        terreno, _ = TerrenoModel.objects.get_or_create(
                            socio=socio,
                            barrio=barrio,
                            defaults={"direccion": f"Lote Principal - {barrio.nombre}"}
                        )

                        # Crear Medidor Default
                        codigo_medidor = f"TEMP-{cedula}"
                        medidor, _ = MedidorModel.objects.get_or_create(
                            codigo=codigo_medidor,
                            defaults={"marca": "GENERICO", "estado": "ACTIVO"}
                        )
                        
                        # Crear Servicio
                        ServicioModel.objects.create(
                            socio=socio,
                            terreno=terreno,
                            tipo="MEDIDO",
                            estado="ACTIVO",
                            valor_tarifa=3.00
                        )
                        # Vincular medidor al terreno (OneToOne/FK logic check)
                        # En tu modelo MedidorModel tiene OneToOne a Terreno o viceversa?
                        # Revisando tu modelo: MedidorModel tiene 'terreno = OneToOneField(...)'
                        medidor.terreno = terreno
                        medidor.save()

                    created_count += 1
                    # self.stdout.write(f"   ✅ Procesado: {nombre_completo}")

            except Exception as e:
                errors.append(f"{cedula} - {nombre_completo}: {str(e)}")
                self.stdout.write(self.style.ERROR(f"   ❌ Error en {cedula}: {str(e)}"))

        # --- 4. REPORTE FINAL ---
        self.stdout.write(self.style.SUCCESS(f"\n✨ PROCESO COMPLETADO"))
        self.stdout.write(f"Socios procesados exitosamente: {created_count}")
        
        if errors:
            self.stdout.write(self.style.ERROR(f"\n⚠️ REGISTROS OMITIDOS ({len(errors)}):"))
            for err in errors:
                self.stdout.write(f"   - {err}")
