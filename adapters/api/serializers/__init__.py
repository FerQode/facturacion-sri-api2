# adapters/api/serializers/__init__.py
from .comercial_serializers import (
    CatalogoRubroSerializer,
    ProductoMaterialSerializer,
    SocioSerializer,
    FacturaSerializer,
    DetalleFacturaSerializer,
    PagoSerializer,
    DetallePagoSerializer
)

__all__ = [
    'CatalogoRubroSerializer',
    'ProductoMaterialSerializer',
    'SocioSerializer',
    'FacturaSerializer',
    'DetalleFacturaSerializer',
    'PagoSerializer',
    'DetallePagoSerializer',
]
