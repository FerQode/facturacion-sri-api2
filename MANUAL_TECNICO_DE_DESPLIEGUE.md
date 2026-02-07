# 🛠️ MANUAL TÉCNICO DE DESPLIEGUE | ERP EL ARBOLITO

> **Versión:** 1.0 Release Candidate  
> **Fecha:** Febrero 2026  
> **Autor:** Equipo de Desarrollo (Tesis de Grado)  
> **Plataforma Objetivo:** Windows 10/11 (Localhost)

---

## 1. Resumen de Arquitectura (Justificación Técnica)

El sistema **"ERP El Arbolito"** implementa una **Arquitectura Híbrida y Modular** diseñada para garantizar el cumplimiento estricto de la normativa del SRI (Servicio de Rentas Internas):

1.  **Backend Core (Django 5 + Python 3.12):** Maneja la lógica de negocio, ORM transaccional, API RESTful y reglas de facturación.
2.  **Micro-Componente de Firma (Java Interop):**
    *   *Justificación:* El SRI exige el estándar de firma **XAdES-BES**.
    *   *Implementación:* Se integra un componente `jar` (`sri.jar`) ejecutado mediante `subprocess` desde Python. Esto permite utilizar las robustas librerías criptográficas de Java (Bouncy Castle) que garantizan la validez legal del XML.
3.  **Motor de Reportes (WeasyPrint):**
    *   Utiliza librerías de renderizado web (Pango/Cairo) para convertir HTML/CSS modernos en documentos PDF (RIDE) de alta fidelidad.

---

## 2. Prerrequisitos del Sistema (Lista de Verificación)

Para garantizar el funcionamiento de los 3 módulos anteriores, su entorno **DEBE** contar con el siguiente software. 

### 📦 Software Base
*   **[Python 3.12.x](https://www.python.org/downloads/)**: Lenguaje principal. **Importante:** Marcar "Add Python to PATH" durante la instalación.
*   **[Git SCM](https://git-scm.com/download/win)**: Para clonar el repositorio.
*   **[MySQL Server 8.0](https://dev.mysql.com/downloads/installer/)**: Motor de Base de Datos.

### ⚠️ Componentes CRÍTICOS (Sin esto, el sistema fallará)

#### ☕ 1. Java Runtime Environment (JRE 8+)
*   **Requerido para:** Módulo de Firma Electrónica (`sri.jar`).
*   **Síntoma de fallo:** Error 500 al intentar autorizar una factura ("Java command not found").
*   **Descarga:** [Java JRE Oficial](https://www.java.com/es/download/)

#### 🖨️ 2. GTK3 Runtime for Windows
*   **Requerido para:** Motor de PDFs (WeasyPrint).
*   **Explicación:** WeasyPrint depende de librerías gráficas de Linux (Cairo/Pango). En Windows, estas deben instalarse manulamente.
*   **Síntoma de fallo:** `OSError: dlopen() failed` o `library not found` al generar PDF.
*   **Descarga (Instalador MSI):**  
    👉 **[GTK3 Runtime Installer (Latest Release)](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)**  
   *(Descargue el archivo `.exe` más reciente y reinicie su terminal tras instalar).*

---

## 3. Gestión de Credenciales y Seguridad

> 🛡️ **NOTA DE SEGURIDAD:** 
> Por políticas de *DevSecOps* y protección de datos, el archivo de Firma Electrónica real (`.p12`) **NO** se encuentra en el repositorio público de GitHub.

### Instrucciones para el Revisor:
1.  **Descargar Firma de Prueba:** Acceda al repositorio seguro de Google Drive para obtener el archivo `firma_tesis.p12` y la contraseña de prueba.
    *   📂 **Enlace Seguro:** `[https://drive.google.com/drive/folders/11B0os83EAMVororvKq7LgPI1bvzn4fRx?usp=sharing]`
2.  **Ubicación:** Una vez descargado, **copie el archivo `firma_tesis.p12` en la RAÍZ del proyecto** (al mismo nivel que `manage.py`).

---

## 4. Guía de Instalación Paso a Paso

Abra una terminal **PowerShell** (como Administrador preferiblemente) y ejecute:

### 4.1. Obtención del Código
```powershell
git clone https://github.com/FerQode/facturacion-sri-api2.git
cd facturacion-sri-api2
```

### 4.2. Configuración del Entorno Virtual
```powershell
# Crear entorno aislado
python -m venv venv

# Activar entorno
.\venv\Scripts\activate
```

### 4.3. Instalación de Dependencias
```powershell
pip install -r requirements.txt
```
*(Si ya instaló GTK3, este paso debería fluir sin errores de compilación).*

### 4.4. Configuración de Variables (.env)
Cree un archivo llamado `.env` en la raíz y pegue esta configuración. Asegúrese de que `SRI_FIRMA_PATH` coincida con el nombre del archivo descargado en el paso 3.

```ini
DEBUG=True
SECRET_KEY=clave-insegura-dev-mode
ALLOWED_HOSTS=*

# Base de Datos (Ajuste su contraseña de root si es diferente)
DATABASE_URL=mysql://root:root@127.0.0.1:3306/db_tesis

# Configuración SRI (Ambiente de Pruebas Mockeado)
SRI_AMBIENTE=1
SRI_EMISOR_RUC=1722253331001
SRI_EMISOR_RAZON_SOCIAL="JUNTA AGUA POTABLE EL ARBOLITO"
SRI_NOMBRE_COMERCIAL="EL ARBOLITO"
SRI_EMISOR_DIRECCION_MATRIZ="Latacunga - Ecuador"
SRI_OBLIGADO_CONTABILIDAD="NO"

# Secuenciales
SRI_SERIE_ESTABLECIMIENTO=001
SRI_SERIE_PUNTO_EMISION=001
SRI_SECUENCIA_INICIO=1

# Firma Electrónica (Asegúrese de tener firma_tesis.p12 en la raíz)
SRI_FIRMA_PATH=firma_tesis.p12
SRI_FIRMA_PASS=TestPass123
# URLs del SRI (Web Services)
SRI_URL_RECEPCION=https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl
SRI_URL_AUTORIZACION=https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl
```

---

## 5. Despliegue de Base de Datos

En MySQL Workbench (o CLI), ejecute una sola vez:
```sql
CREATE DATABASE db_tesis;
```

Luego, en su terminal del proyecto:
```powershell
# Crear tablas
python manage.py migrate

# Crear administrador
python manage.py createsuperuser
# (Usuario: admin, Clave: admin)
```

---

## 6. Pruebas de Validación (Smoke Tests)

Levante el servidor de desarrollo:
```powershell
python manage.py runserver
```

### ✅ Prueba 1: Acceso Administrativo
1.  Navegue a: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
2.  Logueese. Si ve el panel dashboard, la **BD y Django** funcionan.

### ✅ Prueba 2: Generación de RIDE (PDF) - "La Prueba de Fuego"
Esta prueba verifica que **WeasyPrint, GTK3 y los modelos** estén integrados.
1.  En el Admin, vaya a **"Facturas"** y cree una factura manualmente (o use una existente).
2.  Copie el ID de esa factura (ej: 1).
3.  Vaya a: `http://127.0.0.1:8000/api/v1/facturas/1/pdf/`
4.  **Resultado esperado:** El navegador debe descargar o visualizar un archivo PDF con formato de factura.
    *   *Si esto funciona, su instalación es 100% exitosa.*

---

## 7. Solución de Problemas (Troubleshooting)

| Error Común | Causa Probable | Solución |
| :--- | :--- | :--- |
| `OSError: dlopen() failed` | No se encuentra GTK3 | Instale el [GTK3 Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) y reinicie consola. |
| `FileNotFoundError: 'java'` | Java no está en el PATH | Instale JRE 8+ y verifique con `java -version`. |
| `Error config: SRI_FIRMA_PATH` | Falta el archivo .p12 | Descargue la firma del Drive y péguela en la raíz como `firma_tesis.p12`. |
| `mysql_config not found` (Pip) | Falta conector C++ | Asegúrese de instalar MySQL en modo "Developer" o use el binario precompilado de wheel. |

---
**Departamento de Ingeniería de Software**  
*Proyecto Tesis "El Arbolito"*
