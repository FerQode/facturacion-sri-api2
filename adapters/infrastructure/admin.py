# adapters/infrastructure/admin.py
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from core.shared.enums import EstadoAsistencia, EstadoJustificacion, EstadoSolicitud, EstadoEvento, TipoRubro, EstadoCuentaPorCobrar

# 1. Importamos los modelos
from .models import (
    SocioModel,
    MedidorModel,
    LecturaModel,
    BarrioModel,
    TerrenoModel,
    FacturaModel,
    DetalleFacturaModel,
    MultaModel,
    PagoModel, # Cabecera
    # DetallePagoModel, # No se exporta en __init__ aún, cuidado. Lo importamos de models.pago_model si es necesario, o actualizamos __init__
    ServicioModel,
    EventoModel,
    AsistenciaModel,
    SRISecuencialModel,
    CatalogoRubroModel,
    CuentaPorCobrarModel,
    OrdenTrabajoModel,
    ProductoMaterial,
    SolicitudJustificacionModel
)
# Hack: Importar el detalle directamente si no está en __init__
from adapters.infrastructure.models.pago_model import DetallePagoModel

@admin.register(BarrioModel)
class BarrioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre') 
    search_fields = ('nombre',)

@admin.register(SocioModel)
class SocioAdmin(SimpleHistoryAdmin):
    list_display = ('identificacion', 'apellidos', 'nombres', 'barrio', 'modalidad_cobro', 'esta_activo')
    list_filter = ('rol', 'esta_activo', 'barrio', 'modalidad_cobro')
    search_fields = ('identificacion', 'nombres', 'apellidos')
    ordering = ['apellidos'] 

    fieldsets = (
        ('Identificación', {
            'fields': ('identificacion', 'nombres', 'apellidos', 'tipo_identificacion')
        }),
        ('Contacto', {
            'fields': ('email', 'email_notificacion', 'telefono', 'barrio', 'direccion')
        }),
        ('Sistema', {
            'fields': ('rol', 'esta_activo', 'modalidad_cobro', 'usuario')
        }),
        ('Social/Legal', {
            'fields': ('es_tercera_edad', 'tiene_discapacidad', 'en_litigio')
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
class LecturaAdmin(SimpleHistoryAdmin):
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
class MultaAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'socio', 'motivo', 'valor', 'estado', 'fecha_registro')
    list_filter = ('estado', 'fecha_registro')
    search_fields = ('socio__nombres', 'socio__identificacion', 'motivo')
    list_editable = ('estado',)

# --- ✅ SECCIÓN DE FACTURACIÓN Y PAGOS ---

class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFacturaModel
    extra = 0
    readonly_fields = ('subtotal',)

# class PagoInline(admin.TabularInline):
#     model = PagoModel
#     extra = 0
#     can_delete = False
#     readonly_fields = ('fecha_registro',)
# YA NO USAMOS PAGO INLINE DENTRO DE FACTURA SI EL PAGO ES MAESTRO-DETALLE GLOBAL
# OJO: Si el modelo PagoModel ya no tiene FK a Factura, no se puede poner Inline aquí.

@admin.register(FacturaModel)
class FacturaAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'get_socio', 'fecha_emision', 'total', 'estado', 'es_fiscal', 'estado_sri')
    list_filter = ('estado', 'es_fiscal', 'estado_sri', 'fecha_emision')
    search_fields = ('socio__identificacion', 'clave_acceso_sri') 
    
    inlines = [DetalleFacturaInline]

    def get_socio(self, obj):
        if hasattr(obj, 'socio'):
            return f"{obj.socio.nombres} {obj.socio.apellidos}"
        return "N/A"

# --- ✅ PAGO MAESTRO DETALLE ---

class DetallePagoInline(admin.TabularInline):
    model = DetallePagoModel
    extra = 1
    min_num = 1

@admin.register(PagoModel)
class PagoAdmin(SimpleHistoryAdmin):
    list_display = ('numero_comprobante_interno', 'socio', 'monto_total', 'fecha_registro', 'validado')
    list_filter = ('fecha_registro', 'validado')
    search_fields = ('numero_comprobante_interno', 'socio__identificacion', 'socio__apellidos')
    autocomplete_fields = ['socio']
    
    inlines = [DetallePagoInline]

# --- ✅ SECCIÓN DE SERVICIOS AGUA (NUEVO) ---
@admin.register(ServicioModel)
class ServicioAguaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_socio_nombre', 'tipo', 'valor_tarifa', 'estado', 'fecha_instalacion')

    list_filter = ('tipo', 'estado', 'fecha_instalacion')
    search_fields = ('socio__nombres', 'socio__apellidos', 'socio__identificacion')
    autocomplete_fields = ['socio', 'terreno']

    def get_socio_nombre(self, obj):
        return f"{obj.socio.nombres} {obj.socio.apellidos}"
    get_socio_nombre.short_description = "Socio"

# --- ✅ FASE 2: GESTIÓN DE EVENTOS Y MINGAS ---

@admin.action(description="👥 Generar lista de asistencia (Todos los socios)")
def generar_asistencia_masiva(modeladmin, request, queryset):
    """
    Crea registros de Asistencia para TODOS los socios activos en el evento seleccionado.
    Default: Estado FALTA (para luego marcar ASISTIO).
    """
    for evento in queryset:
        socios_activos = SocioModel.objects.filter(esta_activo=True)
        creados = 0
        for socio in socios_activos:
            obj, created = AsistenciaModel.objects.get_or_create(
                evento=evento,
                socio=socio,
                defaults={'estado': EstadoAsistencia.FALTA.value} 
            )
            if created:
                creados += 1
        modeladmin.message_user(request, f"✅ Se generaron {creados} boletas de asistencia para: {evento.nombre}")

@admin.action(description="✅ Marcar como ASISTIÓ")
def marcar_presente(modeladmin, request, queryset):
    updated = queryset.update(estado=EstadoAsistencia.ASISTIO.value)
    modeladmin.message_user(request, f"{updated} socios marcados como ASISTIÓ.")

@admin.action(description="❌ Marcar como FALTA (Injustificada)")
def marcar_falta(modeladmin, request, queryset):
    updated = queryset.update(estado=EstadoAsistencia.FALTA.value)
    modeladmin.message_user(request, f"{updated} socios marcados con FALTA.")

@admin.register(EventoModel)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'fecha', 'valor_multa', 'estado')
    list_filter = ('tipo', 'estado', 'fecha')
    search_fields = ('nombre',)
    actions = [generar_asistencia_masiva]

@admin.register(AsistenciaModel)
class AsistenciaAdmin(SimpleHistoryAdmin):
    list_display = ('get_evento', 'get_socio', 'estado')
    list_filter = ('evento', 'estado')
    search_fields = ('socio__nombres', 'socio__apellidos', 'evento__nombre')
    list_editable = ('estado',) 
    actions = [marcar_presente, marcar_falta]
    autocomplete_fields = ['socio', 'evento']

    def get_evento(self, obj):
        return f"{obj.evento.nombre} ({obj.evento.fecha})"
    get_evento.short_description = "Evento"

    def get_socio(self, obj):
        return f"{obj.socio.apellidos} {obj.socio.nombres}"
    get_socio.short_description = "Socio"

@admin.register(SolicitudJustificacionModel)
class SolicitudJustificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'asistencia', 'motivo', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_solicitud')
    search_fields = ('asistencia__socio__nombres', 'motivo')

# --- ✅ FASE 3: SECUENCIALES SRI (NUEVO) ---
@admin.register(SRISecuencialModel)
class SRISecuencialAdmin(admin.ModelAdmin):
    list_display = ('tipo_comprobante', 'secuencia_actual', 'codigo_establecimiento', 'updated_at')
    list_filter = ('tipo_comprobante',)
    search_fields = ('tipo_comprobante',)
    readonly_fields = ('updated_at',)

# --- ✅ NUEVOS MODELOS FASE 0 ---
@admin.register(CatalogoRubroModel)
class CatalogoRubroAdmin(SimpleHistoryAdmin):
    list_display = ('nombre', 'tipo', 'valor_unitario', 'iva', 'activo')
    list_filter = ('tipo', 'activo', 'iva')
    search_fields = ('nombre',)

@admin.register(OrdenTrabajoModel)
class OrdenTrabajoAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'tipo', 'estado', 'servicio', 'fecha_generacion', 'operador_asignado')
    list_filter = ('estado', 'tipo', 'fecha_generacion')
    search_fields = ('servicio__socio__nombres', 'servicio__socio__apellidos')
    autocomplete_fields = ['servicio', 'operador_asignado']

@admin.register(ProductoMaterial)
class ProductoMaterialAdmin(SimpleHistoryAdmin):
    list_display = ('codigo', 'nombre', 'precio_unitario', 'stock_actual', 'activo')
    list_filter = ('activo', 'graba_iva')
    search_fields = ('nombre', 'codigo')
    autocomplete_fields = ['rubro']

@admin.register(CuentaPorCobrarModel)
class CuentaPorCobrarAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'socio', 'rubro', 'saldo_pendiente', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'fecha_vencimiento', 'rubro')
    search_fields = ('socio__nombres', 'rubro__nombre')
    autocomplete_fields = ['socio', 'factura', 'rubro']
