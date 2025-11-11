from django.contrib import admin

# Importamos los modelos que queremos ver en el panel de admin
from .models import SocioModel, MedidorModel, LecturaModel, FacturaModel, DetalleFacturaModel

# Registramos cada modelo
@admin.register(SocioModel)
class SocioAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'cedula', 'barrio', 'esta_activo')
    search_fields = ('nombres', 'apellidos', 'cedula')

@admin.register(MedidorModel)
class MedidorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'socio', 'esta_activo', 'tiene_medidor_fisico')
    list_filter = ('esta_activo', 'tiene_medidor_fisico')

@admin.register(LecturaModel)
class LecturaAdmin(admin.ModelAdmin):
    list_display = ('medidor', 'fecha_lectura', 'lectura_actual_m3', 'consumo_del_mes_m3')
    list_filter = ('fecha_lectura',)

@admin.register(FacturaModel)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'socio', 'fecha_emision', 'estado', 'total', 'estado_sri')
    list_filter = ('estado', 'estado_sri', 'fecha_emision')
    search_fields = ('socio__nombres', 'socio__apellidos', 'id')

# (El DetalleFacturaModel no se registra por separado, 
# se administra "dentro" de la Factura, pero eso es más avanzado)