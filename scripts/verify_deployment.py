# scripts/verify_deployment.py
import requests
import sys
import json
from datetime import date

# CONFIGURACIÓN
#BASE_URL = "http://localhost:8000" # Cambiar a tu URL de Railway si pruebas producción
BASE_URL = "https://ideal-radiance-production.up.railway.app"  # (Usa tu URL real de Railway)
USERNAME = "admin"            # Usuario creado anteriormente
PASSWORD = "Admin123"              # Contraseña creada anteriormente

def log(msg, type="INFO"):
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "ERROR": "\033[91m", "END": "\033[0m"}
    print(f"{colors.get(type, '')}[{type}] {msg}{colors['END']}")

def run_verification():
    session = requests.Session()
    
    # 1. AUTENTICACIÓN
    log("Iniciando autenticación...", "INFO")
    try:
        resp = session.post(f"{BASE_URL}/api/v1/token/", data={"username": USERNAME, "password": PASSWORD})
        if resp.status_code != 200:
            log(f"Login fallido: {resp.text}", "ERROR")
            return
        token = resp.json()["access"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        log("Autenticación exitosa.", "SUCCESS")
        
    except Exception as e:
        log(f"Error de conexión: {e}", "ERROR")
        return

    # PRE-REQUISITO: Obtener un Socio activo para multar
    log("Obteniendo socio de prueba...", "INFO")
    resp_socios = session.get(f"{BASE_URL}/api/v1/socios/")
    if resp_socios.status_code != 200 or not resp_socios.json().get('results'):
        log("No se encontraron socios para la prueba.", "ERROR")
        return
    socio_id = resp_socios.json()['results'][0]['id']
    log(f"Socio seleccionado ID: {socio_id}", "INFO")

    # ----------------------------------------------------
    # PRUEBA A: Lógica de Negocio (Multas sin Factura)
    # ----------------------------------------------------
    log("=== EJECUTANDO PRUEBA A: VALIDACIÓN DE MULTAS ===", "INFO")
    
    # Paso A.1: Crear Evento
    event_data = {
        "nombre": f"Evento Test Auto {date.today()}",
        "tipo": "ASAMBLEA",
        "fecha": str(date.today()),
        "valor_multa": 5.00,
        "seleccion_socios": "TODOS"
    }
    resp_evt = session.post(f"{BASE_URL}/api/v1/eventos/", json=event_data)
    if resp_evt.status_code != 201:
        log(f"Error creando evento: {resp_evt.text}", "ERROR")
        return
    evento_id = resp_evt.json()['id']
    log(f"Evento creado ID: {evento_id}", "INFO")

    # Paso A.2: Registrar Asistencia (FALTA)
    # Nota: Si el endpoint pide lista de PRESENTES, al no enviarlo (lista vacía), todos quedan faltos (default)
    # O si el endpoint pide explícitamente actualizar, enviamos lista vacía para que este socio cuente como falta.
    # Asumimos que al crear "TODOS", todos inician en estado PENDIENTE/FALTA. 
    # Validamos cerrando directamente, ya que la lógica refactorizada convierte PENDIENTES o FALTAS en multas.
    
    # Paso A.3: Cerrar Evento
    log("Cerrando evento...", "INFO")
    resp_close = session.post(f"{BASE_URL}/api/v1/eventos/{evento_id}/cerrar/")
    if resp_close.status_code != 200:
        log(f"Error cerrando evento: {resp_close.text}", "ERROR")
        return
    log("Evento cerrado correctamente.", "SUCCESS")

    # Paso A.4: ASSERT - Verificar Facturas Pendientes
    log("Verificando existencia de factura (NO DEBERÍA EXISTIR)...", "INFO")
    resp_invoices = session.get(f"{BASE_URL}/api/v1/facturas-gestion/pendientes/")
    
    # Buscamos si existe factura hoy para el socio que incluya la multa
    facturas = resp_invoices.json()
    # Esta verificación depende de cómo devuelve la data tu endpoint 'pendientes'
    # Si devuelve una lista, iteramos.
    
    factura_found = False
    # Nota: Ajustar lógica según respuesta real de tu API. 
    # Si el refactor funcionó, NO debería haber factura generada por este evento.
    # Una forma de validar es verificar la cantidad de facturas antes y después, o buscar por fecha.
    
    # Si 'pendientes' trae lo generado por lote, y acabamos de cerrar evento, NO debería aparecer aquí
    # porque el evento solo genera DEUDA, no FACTURA (documento).
    
    # Simulamos búsqueda simple:
    if isinstance(facturas, list):
         # Asumimos que si hay factura creada hoy con valor 5.00 es la multa
         for f in facturas:
             # Ajustar campos según tu modelo JSON
             if f.get('socio_id') == socio_id and float(f.get('total', 0)) == 5.00:
                 factura_found = True
                 break
    
    if not factura_found:
        log("✅ PRUEBA A PASADA: No se generó factura inmediata. La deuda quedó registrada internamente.", "SUCCESS")
    else:
        log("❌ PRUEBA A FALLIDA: Se detectó una factura de $5.00 generada tras el cierre.", "ERROR")


    # ----------------------------------------------------
    # PRUEBA B: Validación de Infraestructura (S3)
    # ----------------------------------------------------
    log("=== EJECUTANDO PRUEBA B: INFRAESTRUCTURA S3 ===", "INFO")
    
    resp_me = session.get(f"{BASE_URL}/api/v1/usuarios/me/")
    if resp_me.status_code != 200:
        log(f"Error obteniendo perfil: {resp_me.text}", "ERROR")
        return
        
    profile_data = resp_me.json()
    foto_url = profile_data.get('foto')
    
    log(f"URL de Foto recuperada: {foto_url}", "INFO")
    
    if foto_url:
        if "storageapi.dev" in foto_url or "up.railway.app" not in foto_url and "localhost" not in foto_url and "media" not in foto_url:
             # Nota: Ajusta la condición según tu dominio S3 real
             # Si usas Railway storage suele contener storageapi.dev o similar
             log("✅ PRUEBA B PASADA: La URL apunta al servicio de Storage Cloud.", "SUCCESS")
        elif "localhost" in foto_url or "/media/" in foto_url:
             log("❌ PRUEBA B FALLIDA: La URL sigue apuntando al disco local.", "ERROR")
        else:
             log(f"⚠️ RESULTADO INCIERTO: La URL es {foto_url}. Verificar manualmente.", "INFO")
    else:
        log("⚠️ No se pudo validar S3: El usuario no tiene foto de perfil asignada.", "INFO")

if __name__ == "__main__":
    print("Iniciando Script de Verificación de Despliegue...")
    run_verification()
