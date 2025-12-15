# adapters/infrastructure/admin.py
from django.contrib import admin

# Importamos los modelos que queremos ver en el panel de admin
from .models import SocioModel, MedidorModel, LecturaModel, FacturaModel, DetalleFacturaModel, BarrioModel

# Registramos cada modelo con configuraciones personalizadas para facilitar la gestión

@admin.register(BarrioModel)
class BarrioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(SocioModel)
class SocioAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'cedula', 'barrio', 'rol', 'esta_activo')
    list_filter = ('rol', 'esta_activo', 'barrio')
    search_fields = ('nombres', 'apellidos', 'cedula')
    # Opcional: Mostrar el usuario vinculado en el detalle
    readonly_fields = ('usuario',)

@admin.register(MedidorModel)
class MedidorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'socio', 'esta_activo', 'tiene_medidor_fisico')
    list_filter = ('esta_activo', 'tiene_medidor_fisico')
    search_fields = ('codigo', 'socio__nombres', 'socio__apellidos', 'socio__cedula')

@admin.register(LecturaModel)
class LecturaAdmin(admin.ModelAdmin):
    list_display = ('medidor', 'fecha_lectura', 'lectura_actual_m3', 'consumo_del_mes_m3')
    list_filter = ('fecha_lectura',)
    search_fields = ('medidor__codigo',)

class DetalleFacturaInline(admin.TabularInline):
    """Permite ver y editar los detalles DENTRO de la pantalla de la Factura"""
    model = DetalleFacturaModel
    extra = 0 # No mostrar filas vacías extra
    readonly_fields = ('subtotal',) # El subtotal debería ser calculado, mejor no editarlo a mano

@admin.register(FacturaModel)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'socio', 'fecha_emision', 'estado', 'total', 'estado_sri')
    list_filter = ('estado', 'estado_sri', 'fecha_emision')
    search_fields = ('socio__nombres', 'socio__apellidos', 'id', 'clave_acceso_sri')
    
    # Añadimos los detalles como una tabla dentro de la factura
    inlines = [DetalleFacturaInline]
    
    # Hacemos que los campos del SRI sean de solo lectura para evitar manipulación manual
    readonly_fields = ('xml_enviado_sri', 'xml_respuesta_sri', 'clave_acceso_sri')