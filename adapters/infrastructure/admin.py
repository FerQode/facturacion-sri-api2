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
    # ACTUALIZADO: Referencias correctas a la Fase 1 y 2
    list_display = ('cedula', 'apellidos', 'nombres', 'barrio_domicilio', 'rol', 'esta_activo')
    list_filter = ('rol', 'esta_activo', 'barrio_domicilio')
    search_fields = ('cedula', 'nombres', 'apellidos')
    
    # Esto es necesario para que funcione el 'autocomplete_fields' en TerrenoAdmin
    ordering = ['apellidos'] 

    fieldsets = (
        ('Identificación', {
            'fields': ('cedula', 'nombres', 'apellidos')
        }),
        ('Contacto', {
            'fields': ('email', 'telefono', 'barrio_domicilio', 'direccion')
        }),
        ('Sistema', {
            'fields': ('rol', 'esta_activo', 'usuario')
        }),
    )

@admin.register(TerrenoModel)
class TerrenoAdmin(admin.ModelAdmin):
    # ACTUALIZADO: Fase 3 (Gestión de Terrenos)
    list_display = ('id', 'get_socio_nombre', 'barrio', 'direccion', 'es_cometida_activa')
    list_filter = ('es_cometida_activa', 'barrio')
    search_fields = ('direccion', 'socio__cedula', 'socio__apellidos')
    
    # Autocompletado: Requiere que SocioAdmin y BarrioAdmin tengan 'search_fields'
    autocomplete_fields = ['socio', 'barrio']

    def get_socio_nombre(self, obj):
        return f"{obj.socio.apellidos} {obj.socio.nombres}"
    get_socio_nombre.short_description = "Socio Propietario"

@admin.register(MedidorModel)
class MedidorAdmin(admin.ModelAdmin):
    # ACTUALIZADO: Fase 4 (Campos nuevos: marca, estado, terreno)
    list_display = ('codigo', 'estado', 'marca', 'lectura_inicial', 'get_ubicacion')
    list_filter = ('estado', 'marca')
    search_fields = ('codigo', 'terreno__socio__cedula')
    
    # Campo calculado para ver dónde está instalado
    def get_ubicacion(self, obj):
        if obj.terreno:
            return f"{obj.terreno.barrio.nombre} - {obj.terreno.direccion}"
        return "⚠️ EN BODEGA / RETIRADO"
    get_ubicacion.short_description = "Ubicación Actual"

@admin.register(LecturaModel)
class LecturaAdmin(admin.ModelAdmin):
    # ACTUALIZADO: Corrección crítica de nombres de campos (Fase 4.5)
    # Antes: lectura_actual_m3 -> Ahora: valor
    # Antes: fecha_lectura -> Ahora: fecha
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