# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.1.0] - 2026-02-07

### Added
- **Infrastructure:** New `Inventario` module with `ProductoMaterial` model for POS sales.
- **Governance:** Implemented `Evento` (Mingas/Asambleas) and `Asistencia` models for community tracking.
- **Reconnections:** Added `OrdenTrabajo` model to manage physical service reconnections.
- **Documentation:** Integrated `drf-spectacular` for OpenAPI 3.0 support.
    - Swagger UI available at `/api/docs/`.
    - Redoc available at `/api/redoc/`.

### Changed
- **Architecture:** Complete refactor to Clean Architecture (Domain-Driven Design).
- **Billing:** `PagoModel` refactored to Master-Detail structure (`Pago` + `DetallePago`) supporting mixed payment methods.
- **Socios:** Updated `SocioModel` to support Hybrid Billing (Fixed Rate vs Metered) and social flags.
- **API:** Modularized monolithic `views.py` into `adapters/api/views/` package.
- **Settings:** Centralized API URL configuration under `/api/v1/` prefix.

### Removed
- **Legacy:** Squashed old migrations to clean state (`0001_initial`, `0002_...`).
- **Cleanup:** Removed unused serializer files and monolithic view structures.

### Security
- **Auth:** Enforced `IsAuthenticated` permission on all commercial endpoints.
- **Transactions:** Implemented `transaction.atomic` for payment processing to ensure data integrity.
