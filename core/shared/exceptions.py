"""
Excepciones de Negocio Personalizadas.

Estas excepciones son usadas por los Casos de Uso para
señalar errores de negocio específicos, permitiendo que
la capa de API (las Vistas) las atrape y devuelva
respuestas HTTP correctas (ej: 404, 400).
"""

class BaseExcepcionDeNegocio(Exception):
    """Excepción base para nuestros errores de dominio."""
    pass

# --- Errores de Entidad (404 Not Found) ---

class SocioNoEncontradoError(BaseExcepcionDeNegocio):
    pass

class MedidorNoEncontradoError(BaseExcepcionDeNegocio):
    pass

class LecturaNoEncontradaError(BaseExcepcionDeNegocio):
    pass

class FacturaNoEncontradaError(BaseExcepcionDeNegocio):
    pass

# --- Errores de Regla de Negocio (400 Bad Request) ---

class FacturaEstadoError(BaseExcepcionDeNegocio):
    """Usado cuando se intenta pagar una factura ya pagada, etc."""
    pass

class ValidacionError(BaseExcepcionDeNegocio):
    """Usado para errores de validación de datos de entrada."""
    pass