# 📝 Plan de Documentación Técnica Profesional (Nivel Tesis)

## Objetivo
Elevar la documentación del proyecto "ERP El Arbolito" a estándares de **Ingeniería de Software Senior**, migrando de Swagger 2.0 (`drf-yasg`) a **OpenAPI 3.1 (`drf-spectacular`)** y generando manuales de usuario/arquitectura para la defensa de tesis.

## 🔎 Diagnóstico Actual
*   **Estado:** `drf-yasg` instalado (OpenAPI 2.0 Legacy).
*   **Problema:** Documentación automática básica, sin descripciones detalladas de endpoints, ejemplos de respuesta ni esquemas de error profesional.
*   **Meta:** "Silicon Valley Standard" -> OpenAPI 3.0, autogeneración de esquemas y manuales PDF.

---

## 📅 Roadmap de Implementación (Fase por Fase)

### Fase 1: Modernización del Core (Migración a OpenAPI 3.0)
*Objetivo: Reemplazar el motor de documentación antiguo por el estándar moderno.*
1.  **Instalación:** `pip install drf-spectacular`.
2.  **Configuración:** Reemplazar `drf_yasg` en `INSTALLED_APPS` y configurar `REST_FRAMEWORK` settings.
3.  **Routing:** Actualizar `config/urls.py` para exponer `schema`, `swagger-ui` y `redoc` versión 3.

### Fase 2: "Decoración" de la API (Documentación en Código)
*Objetivo: Que el código sea la fuente de la verdad.*
1.  **Refactor de Vistas:** Iterar sobre controladores clave (`FacturaViews`, `SocioViews`, `SRIViews`).
2.  **Anotaciones (@extend_schema):**
    *   Agregar `summary` y `description` detallada.
    *   Definir códigos de estado HTTP (200, 400, 404, 500).
    *   Añadir ejemplos de JSON (Request/Response).
3.  **Tags:** Organizar endpoints por módulos (Facturación, Reportes, Gobernanza).

### Fase 3: Generación de Entregables (Exportación)
*Objetivo: Generar los archivos físicos para el CD/Entregable.*
1.  **Schema Dump:** Exportar `api_schema.yaml` usando `python manage.py spectacular`.
2.  **HTML Estático:** Convertir el YAML a un archivo `documentation.html` portable (usando Redoc CLI).
3.  **PDF (Opcional):** Generar versión PDF para imprimir si el docente lo exige.

### Fase 4: Documentación Complementaria (Tesis)
*Objetivo: Cubrir la vista de Usuario y Arquitectura.*
1.  **Manual de Usuario Final:**
    *   Enfoque funcional (Pantalla por Pantalla).
    *   Flujo: "Cómo crear una factura", "Cómo anular", "Cómo ver reportes".
2.  **Manual de Arquitectura:**
    *   Diagramas C4 / UML.
    *   Justificación de decisiones técnicas (Django, WeasyPrint, Java Bridge).

---

## ✅ Lista de Verificación (Definition of Done)
- [ ] `drf-spectacular` instalado y operativo.
- [ ] Swagger UI muestra ejemplos reales de Facturas y Errores.
- [ ] Endpoint de descarga de PDF (`/api/v1/facturas/{id}/pdf/`) documentado como `binary/pdf`.
- [ ] Archivo `api_schema.yaml` generado en la raíz.
- [ ] `MANUAL_USUARIO.md` creado con flujos básicos.

## 👥 User Review Required
> [!IMPORTANT]
> Esta migración implica eliminar `drf-yasg`. Si tienes lógica personalizada compleja dependiente de yasg, avísame. De lo contrario, procederé con el reemplazo limpio.
