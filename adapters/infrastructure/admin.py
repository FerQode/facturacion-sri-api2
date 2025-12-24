from django.contrib import admin

# 1. Importamos los modelos
# (Asegúrate de que FacturaModel y DetalleFacturaModel existan en models/__init__.py)
from .models import (
    SocioModel, 
    MedidorModel, 
    LecturaModel, 
    BarrioModel, 
    TerrenoModel,
    FacturaModel,        # Si aún no has creado este archivo, coméntalo
    DetalleFacturaModel  # Si aún no has creado este archivo, coméntalo
)

@admin.register(BarrioModel)
class BarrioAdmin(admin.ModelAdmin):
    # Usamos 'id' y 'nombre' que son seguros. 
    # Si tienes 'activo' en el modelo, descomenta la línea de abajo.
    list_display = ('id', 'nombre') 
    search_fields = ('nombre',)

@admin.register(SocioModel)
class SocioAdmin(admin.ModelAdmin):
    # --- CORRECCIÓN: Usamos 'barrio' en lugar de 'barrio_domicilio' ---
    list_display = ('cedula', 'apellidos', 'nombres', 'barrio', 'rol', 'esta_activo')
    
    # Filtros laterales
    list_filter = ('rol', 'esta_activo', 'barrio')
    
    search_fields = ('cedula', 'nombres', 'apellidos')
    ordering = ['apellidos'] 

    fieldsets = (
        ('Identificación', {
            'fields': ('cedula', 'nombres', 'apellidos')
        }),
        ('Contacto', {
            # Aquí también cambiamos a 'barrio'
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
    search_fields = ('direccion', 'socio__cedula', 'socio__apellidos')
    
    autocomplete_fields = ['socio', 'barrio']

    def get_socio_nombre(self, obj):
        return f"{obj.socio.apellidos} {obj.socio.nombres}"
    get_socio_nombre.short_description = "Socio Propietario"

@admin.register(MedidorModel)
class MedidorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'estado', 'marca', 'lectura_inicial', 'get_ubicacion')
    list_filter = ('estado', 'marca')
    search_fields = ('codigo', 'terreno__socio__cedula')
    
    def get_ubicacion(self, obj):
        if obj.terreno:
            return f"{obj.terreno.barrio.nombre} - {obj.terreno.direccion}"
        return "⚠️ EN BODEGA / RETIRADO"
    get_ubicacion.short_description = "Ubicación Actual"

@admin.register(LecturaModel)
class LecturaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_medidor_codigo', 'fecha', 'valor', 'esta_facturada')
    list_filter = ('fecha', 'esta_facturada')
    search_fields = ('medidor__codigo',)
    ordering = ('-fecha',)

    def get_medidor_codigo(self, obj):
        return obj.medidor.codigo
    get_medidor_codigo.short_description = "Medidor"

# --- FACTURACIÓN (Si ya tienes los modelos creados) ---

class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFacturaModel
    extra = 0
    # Asegúrate que el modelo Detalle tenga 'subtotal' o el campo que quieras mostrar
    # readonly_fields = ('subtotal',) 

@admin.register(FacturaModel)
class FacturaAdmin(admin.ModelAdmin):
    # Asegúrate que FacturaModel tenga relación 'socio' (o 'terreno')
    list_display = ('id', 'fecha_emision', 'estado', 'total', 'estado_sri')
    list_filter = ('estado', 'estado_sri', 'fecha_emision')
    # search_fields = ('socio__cedula', 'clave_acceso_sri') 
    
    inlines = [DetalleFacturaInline]