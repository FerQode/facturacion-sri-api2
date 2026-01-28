# adapters>api>management>commands>init_roles.py
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from adapters.infrastructure.models import (
    SocioModel, MedidorModel, LecturaModel, BarrioModel, TerrenoModel,
    FacturaModel, DetalleFacturaModel, MultaModel, PagoModel, ServicioModel
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Inicializa los Roles (Grupos) y Permisos del sistema ERP conforme a la Matriz de Seguridad'

    def handle(self, *args, **options):
        self.stdout.write("🛡️  Iniciando configuración de Seguridad RBAC...")

        # 1. Definir Grupos
        grupos = {
            'ADMINISTRADOR': 'Gestión Total del Negocio (Presidente)',
            'TESORERO': 'Gestión Financiera (Cobros, Caja, Multas)',
            'OPERADOR': 'Gestión Operativa (Lecturas, Cortes, Mantenimiento)',
            'SOCIO': 'Consulta limitada de su información'
        }

        for nombre, desc in grupos.items():
            group, created = Group.objects.get_or_create(name=nombre)
            if created:
                self.stdout.write(f"   ✅ Grupo creado: {nombre}")
            else:
                self.stdout.write(f"   ℹ️  Grupo existente: {nombre}")

        # 2. Mapeo de Modelos a ContentTypes
        # Usamos los modelos importados para obtener su ContentType dinámicamente
        ct_lectura = ContentType.objects.get_for_model(LecturaModel)
        ct_factura = ContentType.objects.get_for_model(FacturaModel)
        ct_pago = ContentType.objects.get_for_model(PagoModel)
        ct_multa = ContentType.objects.get_for_model(MultaModel)
        ct_socio = ContentType.objects.get_for_model(SocioModel)
        ct_medidor = ContentType.objects.get_for_model(MedidorModel)
        ct_terreno = ContentType.objects.get_for_model(TerrenoModel)
        ct_servicio = ContentType.objects.get_for_model(ServicioModel)
        
        # 3. Asignación de Permisos por Rol

        # --- A. OPERADOR (Fontanero) ---
        # PUEDE: Ver/Crear/Editar Lecturas, Ver Socios, Ver Medidores
        # NO PUEDE: Ver Facturas, Pagos, Dinero.
        operador_perms = [
            # Lecturas: Full Access (excepto quizás borrar, pero lo dejaremos standard)
            Permission.objects.get(content_type=ct_lectura, codename='add_lecturamodel'),
            Permission.objects.get(content_type=ct_lectura, codename='change_lecturamodel'),
            Permission.objects.get(content_type=ct_lectura, codename='view_lecturamodel'),
            # Socios/Medidores: Solo Ver
            Permission.objects.get(content_type=ct_socio, codename='view_sociomodel'),
            Permission.objects.get(content_type=ct_medidor, codename='view_medidormodel'),
            Permission.objects.get(content_type=ct_terreno, codename='view_terrenomodel'),
            Permission.objects.get(content_type=ct_servicio, codename='view_serviciomodel'),
        ]
        self._asignar_permisos('OPERADOR', operador_perms)

        # --- B. TESORERO ---
        # PUEDE: Gestionar Facturas, Pagos, Multas. Ver Lecturas (Auditoría).
        tesorero_perms = [
            # Facturación: Full Access
            Permission.objects.get(content_type=ct_factura, codename='add_facturamodel'),
            Permission.objects.get(content_type=ct_factura, codename='change_facturamodel'),
            Permission.objects.get(content_type=ct_factura, codename='view_facturamodel'),
            # Pagos: Full Access
            Permission.objects.get(content_type=ct_pago, codename='add_pagomodel'),
            Permission.objects.get(content_type=ct_pago, codename='change_pagomodel'),
            Permission.objects.get(content_type=ct_pago, codename='view_pagomodel'),
            # Multas: Full Access
            Permission.objects.get(content_type=ct_multa, codename='add_multamodel'),
            Permission.objects.get(content_type=ct_multa, codename='change_multamodel'),
            Permission.objects.get(content_type=ct_multa, codename='view_multamodel'),
            # Lecturas: Solo Ver (Para explicar reclamos)
            Permission.objects.get(content_type=ct_lectura, codename='view_lecturamodel'),
            # Socios: Ver (Para contactar morosos)
            Permission.objects.get(content_type=ct_socio, codename='view_sociomodel'),
        ]
        self._asignar_permisos('TESORERO', tesorero_perms)

        # --- C. ADMINISTRADOR (Presidente) ---
        # PUEDE: Todo lo de negocio (Socios, Tarifas, etc)
        # Asignamos TODOS los permisos de nuestros modelos de infraestructura
        admin_perms = Permission.objects.filter(content_type__in=[
            ct_socio, ct_medidor, ct_lectura, ct_factura, ct_pago, 
            ct_multa, ct_terreno, ct_servicio
        ])
        self._asignar_permisos('ADMINISTRADOR', list(admin_perms))

        self.stdout.write(self.style.SUCCESS('✅ RBAC Inicializado correctamente.'))

    def _asignar_permisos(self, nombre_grupo, permisos):
        grupo = Group.objects.get(name=nombre_grupo)
        grupo.permissions.set(permisos)
        grupo.save()
        self.stdout.write(f"   🔐 Permisos actualizados para: {nombre_grupo} ({len(permisos)} permisos)")
