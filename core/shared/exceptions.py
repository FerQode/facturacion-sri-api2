"""
Excepciones de Negocio Personalizadas (Core).

Estas excepciones son lanzadas por la capa de Casos de Uso (Domain Layer)
y deben ser atrapadas por la capa de Infraestructura (Views/API) para
convertirlas en respuestas HTTP adecuadas (404, 400, 409, etc.).
"""

class BaseExcepcionDeNegocio(Exception):
    """Excepción raíz para todos los errores controlados del dominio."""
    pass

# =============================================================================
# 1. EXCEPCIONES GENÉRICAS (Para uso rápido en Casos de Uso)
# =============================================================================

class EntityNotFoundException(BaseExcepcionDeNegocio):
    """
    Error genérico cuando no se encuentra una entidad.
    Equivalente a HTTP 404.
    Uso: raise EntityNotFoundException("El barrio con ID 5 no existe.")
    """
    pass

class BusinessRuleException(BaseExcepcionDeNegocio):
    """
    Error genérico cuando se rompe una regla de negocio.
    Equivalente a HTTP 400 Bad Request.
    Uso: raise BusinessRuleException("El medidor ya está asignado.")
    """
    pass


# =============================================================================
# 2. EXCEPCIONES ESPECÍFICAS (Para granularidad y logs detallados)
# =============================================================================

# --- Errores de Entidad No Encontrada (Heredan de la genérica) ---

class SocioNoEncontradoError(EntityNotFoundException):
    pass

class MedidorNoEncontradoError(EntityNotFoundException):
    pass

class LecturaNoEncontradaError(EntityNotFoundException):
    pass

class FacturaNoEncontradaError(EntityNotFoundException):
    pass

# [NUEVO] Agregamos las excepciones para los nuevos módulos
class BarrioNoEncontradoError(EntityNotFoundException):
    pass

class TerrenoNoEncontradoError(EntityNotFoundException):
    pass


# --- Errores de Estado / Lógica (Heredan de la genérica) ---

class FacturaEstadoError(BusinessRuleException):
    """Usado cuando se intenta pagar una factura ya pagada, anulada, etc."""
    pass

class ValidacionError(BusinessRuleException):
    """Usado para errores de validación de datos de entrada manuales."""
    pass

class MedidorDuplicadoError(BusinessRuleException):
    """[NUEVO] Cuando se intenta registrar un código de medidor que ya existe."""
    pass