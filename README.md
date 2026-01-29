# 💧 ERP "El Arbolito" - Sistema de Gestión de Agua Potable y Facturación SRI

[![CI Pipeline](https://github.com/FerQode/facturacion-sri-api2/actions/workflows/ci.yml/badge.svg)](https://github.com/FerQode/facturacion-sri-api2/actions/workflows/ci.yml)
![Python Version](https://img.shields.io/badge/python-3.12-blue)
![Django Version](https://img.shields.io/badge/django-5.0-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-Proprietray-red)

## 📋 Resumen Ejecutivo
**ERP El Arbolito** es una plataforma tecnológica de nivel empresarial diseñada para la gestión integral de Juntas de Agua Potable en Ecuador. El sistema moderniza la administración comunitaria mediante la automatización de **Facturación Electrónica (SRI)**, control de gobernanza (asistencias, multas) y herramientas avanzadas de **Inteligencia de Negocios** para la toma de decisiones financieras.

El proyecto ha sido refactorizado desde un monolito tradicional hacia una **Arquitectura Limpia (Clean Architecture)**, garantizando escalabilidad, mantenibilidad y un ciclo de vida de desarrollo profesional (CI/CD).

---

## 🏗️ Arquitectura de Software
Este proyecto sigue estrictamente los principios de **Clean Architecture** para desacoplar las reglas de negocio de los frameworks externos.

### Capas del Sistema:
1.  **Core (Dominio & Casos de Uso):**
    *   Contiene la lógica pura del negocio (ej. `CalcularMulta`, `GenerarXMLFactura`).
    *   No tiene dependencias de Django, BD o HTTP.
2.  **Adapters (Adaptadores de Interfaz):**
    *   **API:** Controladores REST (Django Rest Framework) que exponen los casos de uso.
    *   **Infrastructure:** Implementaciones concretas de repositorios (Django ORM), servicios de email, y firma electrónica.
3.  **External:**
    *   Base de Datos (MySQL), Cache (Redis), SRI Web Services.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
| :--- | :--- | :--- | :--- |
| **Backend** | Python / Django | 5.0 | Framework Web de Alto Rendimiento |
| **API** | Django Rest Framework | 3.14 | Interfaz RESTful Documentada (Swagger) |
| **Base de Datos** | MySQL | 8.0 | Almacenamiento Transaccional Robusto |
| **Cache & Broker** | Redis | 7.0 | Colas de Tareas (Celery) y Caché |
| **Facturación** | XML / XAdES-BES | SRI 2.1 | Firma Electrónica y Validación SRI |
| **Infraestructura** | Docker | 24+ | Contenedorización para Paridad Dev/Prod |

---

## 🚀 Módulos Críticos

### 1. 🧾 Facturación Electrónica SRI
Motor de emisión de comprobantes autorizado por el Servicio de Rentas Internas.
*   Generación de XML bajo estándar UBL 2.1.
*   Firma electrónica offline (XAdES-BES).
*   Envío asíncrono y validación automática.

### 2. ⚖️ Gobernanza Comunitaria
Digitalización de los procesos operativos de la Junta de Agua.
*   **Lecturas de Consumo:** Validación de rangos y cálculo de excedentes.
*   **Multas Automáticas:** Por inasistencia a mingas/asambleas.
*   **Convenios de Pago:** Refinanciamiento de deuda vencida.

### 3. 📊 Inteligencia de Negocios (BI)
Módulo analítico para la Tesorería.
*   **Cartera Vencida (Aging Report):** Clasificación de deuda por antigüedad (Corriente, 30-90 días, Incobrable).
*   **Cierre de Caja:** Arqueo diario automatizado (Efectivo vs. Transferencias).
*   **Dashboard KPIs:** Métricas en tiempo real de recaudación y morosidad.

### 4. 🔍 Auditoría Forense
Sistema de trazabilidad inmutable.
*   Integración con `django-simple-history`.
*   Registro de **Quién, Cuándo y Qué** cambió en cada modelo crítico (Facturas, Pagos, Lecturas).

---

## ⚙️ Ecosistema DevOps & CI/CD

El proyecto cuenta con un pipeline de **Integración y Despliegue Continuo** (GitHub Actions) que asegura la calidad del código:

1.  **Análisis Estático:** `flake8` revisa el estilo de código (PEP8).
2.  **Pruebas Automatizadas:** Se ejecutan test unitarios con una base de datos efímera.
3.  **Build de Docker:** Se construye la imagen optimizada (`python:3.12-slim`).
4.  **Auto-Deploy Condicional:**
    *   Al hacer push a `main`, si y solo si los tests pasan, se despliega automáticamente a **Railway**.

---

## 💻 Guía de Instalación (Desarrolladores)

Gracias a Docker, no necesitas instalar Python ni MySQL en tu máquina local.

**Requisitos:**
*   Docker Desktop instalado y corriendo.
*   Git.

### Pasos:

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/FerQode/facturacion-sri-api2.git
    cd facturacion-sri-api2
    ```

2.  **Crear archivo de entorno:**
    Crea un archivo `.env` en la raíz (puedes copiar `.env.example`).
    ```env
    DEBUG=True
    DJANGO_SECRET_KEY=tu-clave-secreta-local
    DATABASE_URL=mysql://root:root@db:3306/db_tesis
    REDIS_URL=redis://redis:6379/0
    ```

3.  **Encender el sistema:**
    ```bash
    docker-compose up --build
    ```

4.  **Acceder:**
    *   **API:** http://localhost:8000/api/v1/
    *   **Swagger:** http://localhost:8000/swagger/
    *   **Admin:** http://localhost:8000/admin/

---

## 📅 Roadmap del Proyecto

- [x] **Fase 1:** Refactorización a Clean Architecture.
- [x] **Fase 2:** Motor de Facturación SRI y Notificaciones Email.
- [x] **Fase 3:** Gobernanza (Multas, Asistencias) y Seguridad.
- [x] **Fase 4:** Auditoría, Analytics y Reportes Financieros.
- [x] **Fase 5:** DevOps Completo (Docker, CI/CD).

---

## 🛡️ Seguridad

*   **Hashing de Contraseñas:** PBKDF2 (Estándar Django).
*   **Protección APIs:** JWT (Access + Refresh Tokens).
*   **Headers de Seguridad:** HSTS, X-Frame-Options, CSRF Protection activados en producción.
*   **Secret Management:** Variables de entorno inyectadas en tiempo de ejecución.

---
**Desarrollado como Proyecto de Tesis de Ingeniería de Software.**
*2025 - All Rights Reserved*
