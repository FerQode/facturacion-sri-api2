# 📘 MANUAL DE INSTALACIÓN Y DESPLIEGUE | ERP EL ARBOLITO

**Versión:** 1.0.0  
**Fecha:** Febrero 2026  
**Autor:** Equipo de Desarrollo Tesis  
**Proyecto:** API de Facturación Electrónica SRI (Backend Django)

---

## 1. Introducción

Este documento detalla el procedimiento paso a paso para desplegar el backend del sistema **"ERP El Arbolito"** en un entorno local **Windows 10/11**. 

El sistema es una **API RESTful** construida en Python/Django que gestiona la facturación de agua potable y la integración con el SRI (Servicio de Rentas Internas) del Ecuador. Incluye módulos de generación de PDF (RIDE) y Firma Electrónica (Java).

---

## 2. Prerrequisitos del Sistema (CRÍTICO) ⚠️

Antes de clonar el código, asegúrese de tener instalado el siguiente software. Si su equipo está "limpio", instale en este orden:

### 🐍 1. Python 3.12 (Lenguaje Base)
*   **Descarga:** [Python 3.12.1 Oficial](https://www.python.org/downloads/release/python-3121/)
*   **⚠️ IMPORTANTE:** Al instalar, marque la casilla **"Add Python to PATH"** en la primera pantalla.

### 🐙 2. Git (Control de Versiones)
*   **Descarga:** [Git por Windows](https://git-scm.com/download/win)
*   Instalación: "Siguiente, Siguiente..." (Opciones por defecto).

### 🐬 3. MySQL Server 8.0 (Base de Datos)
*   **Descarga:** [MySQL Installer Community](https://dev.mysql.com/downloads/installer/)
*   Seleccione "Server Only" o "Developer Default".
*   **Credenciales:** Recuerde la contraseña que asigne al usuario `root` (ej: `root` o `1234`).

### ☕ 4. Java JRE 8+ (Para Firma Electrónica)
*   **Descarga:** [Java JRE (Oracle o OpenJDK)](https://www.java.com/es/download/)
*   Necesario para ejecutar el módulo de firma `sri.jar`.
*   *Verificación:* Abra CMD y escriba `java -version`. Debe salir algo.

### 🖨️ 5. GTK3 Runtime (CRÍTICO para PDFs)
*   **¿Por qué?** La librería de reportes (`WeasyPrint`) necesita librerías gráficas de Linux que no existen en Windows por defecto.
*   **Descarga:** [GTK3 Installer for Windows (GitHub)](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe)
*   **Instalación:** Ejecute el instalador y reinicie su computadora (o al menos cierre y abra su terminal) para que se actualice el PATH.

---

## 3. Instalación del Proyecto

Abra una terminal (PowerShell o CMD) y ejecute:

### Paso 1: Clonar el Repositorio
```powershell
# Sitúese en su carpeta de proyectos
cd C:\Users\SuUsuario\Documentos

# Clone el proyecto
git clone https://github.com/FerQode/facturacion-sri-api2.git

# Ingrese al directorio
cd facturacion-sri-api2
```

### Paso 2: Crear Entorno Virtual (Aislamiento)
```powershell
# Crea una carpeta 'venv' con un Python aislado
python -m venv venv

# Active el entorno (Verá (venv) al inicio de la línea)
.\venv\Scripts\activate
```

### Paso 3: Instalar Dependencias
```powershell
# Esto descargará Django, DRF, WeasyPrint, MysqlClient, etc.
pip install -r requirements.txt
```
*Si este paso falla con "Microsoft Visual C++ 14.0 is required", necesita instalar las "Build Tools de Visual Studio".*

---

## 4. Configuración de Base de Datos

Abra **MySQL Workbench** o su terminal de MySQL y ejecute este comando para crear la base vacía:

```sql
CREATE DATABASE db_tesis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 5. Variables de Entorno (.env)

Cree un archivo llamado `.env` en la raíz del proyecto (junto a `manage.py`) y pegue el siguiente contenido. 
**NOTA:** Esta configuración usa datos de prueba (DUMMY) para evitar exponer credenciales reales.

```ini
# --- CONFIGURACIÓN GENERAL ---
DEBUG=True
SECRET_KEY=django-insecure-clave-super-secreta-para-tesis-local-dev
ALLOWED_HOSTS=*

# --- BASE DE DATOS LOCAL ---
# Formato: mysql://usuario:password@host:port/nombre_db
# Cambie 'root:root' por su 'usuario:clave' real de MySQL
DATABASE_URL=mysql://root:root@127.0.0.1:3306/db_tesis

# --- SRI (VARIABLES DE PRUEBA / MOCK) ---
# Usamos ambiente de PRUEBAS (1)
SRI_AMBIENTE=1
SRI_EMISOR_RUC=1722253331001
SRI_EMISOR_RAZON_SOCIAL="JUNTA ADMINISTRADORA DE AGUA POTABLE EL ARBOLITO"
SRI_NOMBRE_COMERCIAL="AGUA POTABLE EL ARBOLITO"
SRI_EMISOR_DIRECCION_MATRIZ="BARRIO EL ARBOLITO - LATACUNGA"
SRI_OBLIGADO_CONTABILIDAD="NO"

# Secuenciales Visuales
SRI_SERIE_ESTABLECIMIENTO=001
SRI_SERIE_PUNTO_EMISION=001
SRI_SECUENCIA_INICIO=1

# Firma Electrónica (SIMULADA PARA LOCAL)
# El sistema detectará que no es válida para producción, pero permitirá generar XMLs
SRI_FIRMA_PASS=TestPass123
SRI_URL_RECEPCION=https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl
SRI_URL_AUTORIZACION=https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl

# Si tiene un archivo .p12 real de pruebas, ponga su ruta absoluta aqui:
# SRI_FIRMA_PATH=C:\Ruta\A\Su\Firma.p12
```

---

## 6. Inicialización del Sistema

Con el `.env` creado y el entorno `(venv)` activo:

### Paso 1: Crear Tablas (Migraciones)
```powershell
python manage.py migrate
```
*Debe ver una lista de "Applying... OK".*

### Paso 2: Crear Usuario Administrador
```powershell
python manage.py createsuperuser
# Ingrese Usuario: admin
# Email: admin@tesis.com
# Password: admin (u otra segura)
```

---

## 7. Ejecución y Verificación

### Iniciar el Servidor
```powershell
python manage.py runserver
```
Verá el mensaje: `Starting development server at http://127.0.0.1:8000/`

### Pruebas de Funcionamiento

1.  **Panel Administrativo:**
    *   Vaya a: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
    *   Ingrese con su superusuario (`admin`).
    *   Verifique que puede ver módulos como "Socios", "Facturas", etc.

2.  **Documentación API (Swagger):**
    *   Vaya a: [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
    *   Aquí verá todos los endpoints disponibles.

3.  **Prueba de PDF (RIDE):**
    *   *Nota:* Para esto necesita tener al menos una factura creada. Puede crearla manualmente desde el Admin.
    *   Una vez creada, copie el ID de la factura (ej: 1).
    *   Intente descargar su PDF en: `http://127.0.0.1:8000/api/v1/facturas/1/pdf/`

---

## 🆘 Solución de Problemas Comunes

*   **Error `OSError: dlopen() failed` o `library not found` (WeasyPrint):**
    *   Significa que **NO** instaló GTK3 o no reinició la terminal. Revise el paso 2.5.
*   **Error `mysql_config not found` al instalar pip:**
    *   Asegúrese de haber instalado MySQL Installer completo.
*   **Error `Java not found`:**
    *   Asegúrese de instalar JRE y verificar con `java -version`.

---
**¡Instalación Completada Exitosamente!** 🚀
