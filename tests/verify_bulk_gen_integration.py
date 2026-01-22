import os
import django
import sys
from datetime import date

# Configurar Django
import os
import sys

# Agregamos la raíz del proyecto al PATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from adapters.infrastructure.models import ServicioModel, SocioModel, TerrenoModel, BarrioModel
from core.shared.enums import EstadoFactura

User = get_user_model()

def setup_data():
    print("--- 1. Setup Data ---")
    # 1. Admin User
    admin_user, _ = User.objects.get_or_create(username='admin_test', email='admin@test.com')
    if not admin_user.is_staff:
        admin_user.set_password('admin123')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
    print("Admin user ready.")

    # 2. Socio & Services
    # Necesitamos barrio, terreno y socio
    barrio, _ = BarrioModel.objects.get_or_create(nombre="Barrio Test")
    
    # Crear Socio si no existe
    try:
        socio = SocioModel.objects.get(cedula="9999999999")
    except SocioModel.DoesNotExist:
        # Necesita un usuario
        try:
           user_socio = User.objects.get(username="9999999999")
        except User.DoesNotExist:
           user_socio = User.objects.create_user(username="9999999999", password="user123")
           
        socio = SocioModel.objects.create(
            cedula="9999999999", nombres="Test", apellidos="Socio", 
            usuario=user_socio, barrio=barrio, direccion="Calle Falsa 123"
        )
    
    # Crear Terrenos
    terreno1, _ = TerrenoModel.objects.get_or_create(direccion="Lote L-99", barrio=barrio, socio=socio)
    terreno2, _ = TerrenoModel.objects.get_or_create(direccion="Lote L-100", barrio=barrio, socio=socio)

    # Limpieza Segura (Solo datos de prueba)
    from adapters.infrastructure.models import FacturaModel
    FacturaModel.objects.filter(socio=socio).delete() # Primero facturas para evitar ProtectedError
    ServicioModel.objects.filter(socio=socio).delete()
    
    # Crear 2 Servicios FIJOS
    s1 = ServicioModel.objects.create(
        socio=socio, terreno=terreno1, tipo='FIJO', activo=True
    )
    s2 = ServicioModel.objects.create(
        socio=socio, terreno=terreno2, tipo='FIJO', activo=True
    )
    
    print(f"Services ready: {s1.id}, {s2.id}")
    return admin_user

def run_test():
    admin_user = setup_data()
    client = APIClient()
    client.force_authenticate(user=admin_user)

    print("\n--- 2. First Execution (Generating DEC 2025) ---")
    url = '/api/v1/facturas/generar-fijas/'
    payload = {"anio": 2025, "mes": 12}
    response = client.post(url, payload, format='json')
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")

    print("\n--- 3. Second Execution (Idempotency DEC 2025) ---")
    response2 = client.post(url, payload, format='json')
    print(f"Status: {response2.status_code}")
    print(f"Body: {response2.json()}")

    print("\n--- 4. Third Execution (Generating JAN 2026) ---")
    payload_next = {"anio": 2026, "mes": 1}
    response3 = client.post(url, payload_next, format='json')
    print(f"Status: {response3.status_code}")
    print(f"Body: {response3.json()}")

if __name__ == "__main__":
    run_test()
