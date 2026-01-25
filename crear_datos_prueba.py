# crear_datos_prueba.py
import os
import django
from datetime import date
from decimal import Decimal

# 1. Configurar entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 2. Importar Modelos
from adapters.infrastructure.models import (
    SocioModel, BarrioModel, TerrenoModel, MedidorModel, LecturaModel
)

def run():
    print("🌱 -- INICIANDO SEMILLA DE DATOS --")

    # A. Barrio
    barrio, _ = BarrioModel.objects.get_or_create(nombre="Centro El Arbolito")
    print(f"✅ Barrio creado: {barrio.nombre}")

    # B. Socio (Cliente)
    socio, created = SocioModel.objects.get_or_create(
        cedula="1711223344", 
        defaults={
            "nombres": "CONSUMIDOR",
            "apellidos": "PRUEBA FINAL",
            "telefono": "0991234567",
            "email": "tu_correo_real@gmail.com",
            "barrio": barrio
        }
    )
    if created:
        print(f"✅ Socio creado: {socio.nombres}")
    else:
        print(f"ℹ️ El socio {socio.nombres} ya existía.")

    # C. Terreno
    terreno, created_t = TerrenoModel.objects.get_or_create(
        socio=socio,
        barrio=barrio,
        defaults={
            "direccion": "Calle Larga Nro 123",
            "es_cometida_activa": True
        }
    )
    if created_t:
        print(f"✅ Terreno asignado ID: {terreno.id}")
    else:
        print(f"ℹ️ Terreno ya existente ID: {terreno.id}")

    # D. Medidor
    medidor, created_m = MedidorModel.objects.get_or_create(
        codigo="MED-TEST-001",
        defaults={"terreno": terreno, "marca": "TechFlow", "estado": "ACTIVO"}
    )
    if created_m:
        print(f"✅ Medidor creado: {medidor.codigo}")
    else:
        print(f"ℹ️ Medidor ya existente: {medidor.codigo}")

    # E. Lectura (CORREGIDA SEGÚN TU MODELO REAL)
    # Campos detectados en el error: fecha, valor, lectura_anterior, consumo_del_mes
    
    fecha_lectura = date(2026, 1, 5) # Enero 2026
    lectura_anterior = 1000
    lectura_actual_valor = 1030 # Consumo de 30m3
    consumo = lectura_actual_valor - lectura_anterior

    lectura, created_l = LecturaModel.objects.get_or_create(
        medidor=medidor,
        fecha=fecha_lectura, # <--- CORREGIDO (Antes era periodo_mes/anio)
        defaults={
            "lectura_anterior": lectura_anterior,
            "valor": lectura_actual_valor, # <--- CORREGIDO (Antes era lectura_actual)
            "consumo_del_mes": consumo,    # <--- CALCULADO
            "esta_facturada": False,
            "observacion": "Lectura de prueba generada por script"
        }
    )
    
    print("-" * 40)
    print(f"🚀 DATOS LISTOS.")
    print(f"🆔 ID DE LECTURA PARA POSTMAN: {lectura.id}")
    print(f"📅 Fecha: {lectura.fecha}")
    print(f"💧 Consumo: {lectura.consumo_del_mes} m3")
    print("-" * 40)

if __name__ == '__main__':
    run()