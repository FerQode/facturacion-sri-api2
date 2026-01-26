# Sistema de Gestión de Agua y Facturación Electrónica (Junta El Arbolito)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Django](https://img.shields.io/badge/Django-5.0-green) ![License](https://img.shields.io/badge/License-MIT-lightgrey) ![Status](https://img.shields.io/badge/Status-Development-orange)

## 📄 Descripción
Sistema integral diseñado bajo arquitectura limpia (Clean Architecture) para la gestión de juntas de agua potable y facturación electrónica autorizada por el SRI (Ecuador). Incluye módulos de gobernanza (asambleas, multas), gestión de medidores, y un portal del socio para consulta de deudas "360°".

## 🛠️ Tecnologías
*   **Backend:** Python 3.10+, Django 5.x, Django REST Framework (DRF).
*   **Base de Datos:** MySQL (con soporte `dj-database-url`).
*   **Facturación SRI:** Java Runtime (JRE 11+) para firma digital XAdES-BES.
*   **Autenticación:** JWT (SimpleJWT).
*   **Documentación:** Swagger/OpenAPI (`drf-yasg`).

## 📋 Requisitos Previos
Asegúrate de tener instalado:
*   **Python 3.10** o superior.
*   **MySQL Server** (8.0 recomendado).
*   **Java JDK 11** o superior (Requerido para el firmador `sri.jar`).
*   **Git Bash** (o terminal similar).

## 🚀 Instalación (Paso a Paso)

### 1. Clonar Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd facturacion-sri-api2
```

### 2. Configurar Entorno Virtual
```bash
# Crear entorno
python -m venv venv

# Activar (Windows)
venv\Scripts\activate
# Activar (Linux/Mac)
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuración Crítica (Environment & Secrets)

### Variables de Entorno
1.  Copia el archivo de ejemplo:
    ```bash
    cp .env.example .env
    ```
2.  **IMPORTANTE ⚠️:** Edita `.env` con tus credenciales reales (Base de datos, Correo, SRI).

### Firma Electrónica (SRI) ⚠️
El sistema requiere tu archivo de firma `.p12` para autorizar facturas.
1.  Crea una carpeta llamada `secrets/` en la raíz del proyecto.
2.  Coloca tu archivo `.p12` dentro (ej: `el_arbolito.p12`).
3.  Asegúrate de que la variable `SRI_FIRMA_PATH` en `.env` apunte a este archivo.

> **NOTA DE SEGURIDAD:** La carpeta `secrets/` está ignorada por git. **NUNCA** subas tu firma electrónica al repositorio.

### Archivo JAR (Firmador)
Verifica que el archivo `sri.jar` exista en:
`adapters/infrastructure/files/jar/sri.jar`

---

## 💾 Base de Datos y Datos de Prueba

### 1. Aplicar Migraciones
Crea las tablas en tu base de datos MySQL:
```bash
python manage.py migrate
```

### 2. Cargar Datos "Semilla"
Carga usuarios, barrios, tarifas y medidores de prueba para empezar a trabajar de inmediato:
```bash
python manage.py seed_data
```
*(Este comando creará socios ficticios y configuraciones iniciales)*.

---

## ▶️ Ejecución
Levanta el servidor de desarrollo:
```bash
python manage.py runserver
```
El sistema estará disponible en: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 📚 Documentación API
Una vez levantado el servidor, accede a la documentación interactiva:
*   **Swagger UI:** [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
*   **ReDoc:** [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)
