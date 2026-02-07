from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SocioViewSet, 
    FacturaViewSet, 
    PagoViewSet,
    CatalogoRubroViewSet,
    ProductoMaterialViewSet
)

router = DefaultRouter()
router.register(r'socios', SocioViewSet, basename='socio')
router.register(r'facturas', FacturaViewSet, basename='factura')
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'rubros', CatalogoRubroViewSet, basename='rubro')
router.register(r'inventario', ProductoMaterialViewSet, basename='inventario')

urlpatterns = [
    path('', include(router.urls)),
]