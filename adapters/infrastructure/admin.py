# adapters/infrastructure/admin.py

from django.contrib import admin

# 1. Importamos los modelos
# (Asegúrate de que TODOS existan en models/__init__.py, tal como lo actualizamos antes)
from .models import (
    SocioModel, 
    MedidorModel, 
    LecturaModel, 
    BarrioModel, 
    TerrenoModel,
    FacturaModel,        
    DetalleFacturaModel,
    MultaModel,  # ✅ NUEVO
    PagoModel,   # ✅ NUEVO
    ServicioAguaModel # ✅ NUEVO
)

@admin.register(BarrioModel)
class BarrioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre') 
    search_fields = ('nombre',)

@admin.register(SocioModel)
class SocioAdmin(admin.ModelAdmin):
    list_display = ('identificacion', 'apellidos', 'nombres', 'barrio', 'rol', 'esta_activo')
    list_filter = ('rol', 'esta_activo', 'barrio')
    search_fields = ('identificacion', 'nombres', 'apellidos')
    ordering = ['apellidos'] 

    fieldsets = (
        ('Identificación', {
            'fields': ('identificacion', 'nombres', 'apellidos')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'barrio', 'direccion')
        }),
        ('Sistema', {
            'fields': ('rol', 'esta_activo', 'usuario')
        }),
    )

@admin.register(TerrenoModel)
class TerrenoAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_socio_nombre', 'barrio', 'direccion', 'es_cometida_activa')
    list_filter = ('es_cometida_activa', 'barrio')
    search_fields = ('direccion', 'socio__identificacion', 'socio__apellidos')
    autocomplete_fields = ['socio', 'barrio']

    def get_socio_nombre(self, obj):
        return f"{obj.socio.apellidos} {obj.socio.nombres}"
    get_socio_nombre.short_description = "Socio Propietario"

@admin.register(MedidorModel)
class MedidorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'estado', 'marca', 'lectura_inicial', 'get_ubicacion')
    list_filter = ('estado', 'marca')
    search_fields = ('codigo', 'terreno__socio__identificacion')
    
    def get_ubicacion(self, obj):
        if obj.terreno:
            return f"{obj.terreno.barrio.nombre} - {obj.terreno.direccion}"
        return "⚠️ EN BODEGA / RETIRADO"
    get_ubicacion.short_description = "Ubicación Actual"

@admin.register(LecturaModel)
class LecturaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'get_medidor_codigo', 
        'fecha', 
        'valor', 
        'lectura_anterior',
        'consumo_del_mes',
        'esta_facturada'
    )
    list_filter = ('fecha', 'esta_facturada')
    search_fields = ('medidor__codigo',)
    ordering = ('-fecha',)
    readonly_fields = ('lectura_anterior', 'consumo_del_mes', 'fecha_registro')

    def get_medidor_codigo(self, obj):
        return obj.medidor.codigo
    get_medidor_codigo.short_description = "Medidor"

# --- ✅ SECCIÓN DE MULTAS (NUEVO) ---
@admin.register(MultaModel)
class MultaAdmin(admin.ModelAdmin):
    list_display = ('id', 'socio', 'motivo', 'valor', 'estado', 'fecha_registro')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('socio__nombres', 'socio__identificacion', 'motivo')
    list_editable = ('estado',) # Útil para marcar PAGADA rápido en pruebas

# --- ✅ SECCIÓN DE FACTURACIÓN Y PAGOS ---

class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFacturaModel
    extra = 0
    readonly_fields = ('subtotal',)

class PagoInline(admin.TabularInline):
    """Permite ver los pagos (Efectivo/Transferencia) dentro de la factura"""
    model = PagoModel
    extra = 0
    can_delete = False
    readonly_fields = ('fecha_registro',)

@admin.register(FacturaModel)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_socio', 'fecha_emision', 'total', 'estado', 'estado_sri')
    list_filter = ('estado', 'estado_sri', 'fecha_emision')
    search_fields = ('socio__identificacion', 'sri_clave_acceso') 
    
    # Mostramos Detalles y Pagos en la misma ficha
    inlines = [DetalleFacturaInline, PagoInline]

    def get_socio(self, obj):
        # Ajusta según tu modelo, si socio es FK directa o via terreno
        if hasattr(obj, 'socio'):
            return f"{obj.socio.nombres} {obj.socio.apellidos}"
        return "N/A"

@admin.register(PagoModel)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'factura', 'metodo', 'monto', 'referencia', 'fecha_registro')
    list_filter = ('metodo',)

# --- ✅ SECCIÓN DE SERVICIOS AGUA (NUEVO) ---
@admin.register(ServicioAguaModel)
class ServicioAguaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_socio_nombre', 'tipo', 'valor_tarifa', 'activo', 'fecha_instalacion')
    list_filter = ('tipo', 'activo', 'fecha_instalacion')
    search_fields = ('socio__nombres', 'socio__apellidos', 'socio__identificacion')
    autocomplete_fields = ['socio', 'terreno']

    def get_socio_nombre(self, obj):
        return f"{obj.socio.nombres} {obj.socio.apellidos}"
    get_socio_nombre.short_description = "Socio"
