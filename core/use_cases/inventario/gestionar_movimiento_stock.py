# core/use_cases/inventario/gestionar_movimiento_stock.py
from django.db import transaction
from adapters.infrastructure.models import ProductoMaterial
from enum import Enum

class TipoMovimiento(Enum):
    ENTRADA = 'ENTRADA' # Compra
    SALIDA = 'SALIDA'   # Ajuste / Pérdida / Venta manual

class GestionarMovimientoStockUseCase:
    """
    Caso de uso para movimientos manuales de inventario (Compras, Ajustes).
    No confundir con la venta (que descuenta stock automáticamente).
    """

    @transaction.atomic
    def ejecutar(self, producto_id: int, cantidad: int, tipo: str, observacion: str, costo_unitario: float = None) -> dict:
        try:
            # Bloqueo de fila para evitar condiciones de carrera
            producto = ProductoMaterial.objects.select_for_update().get(id=producto_id)
        except ProductoMaterial.DoesNotExist:
            raise ValueError(f"Producto {producto_id} no encontrado.")

        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva.")

        if tipo == TipoMovimiento.ENTRADA.value:
            producto.stock_actual += cantidad
            # Actualizar precio si es una compra y se provee costo
            # Simple average cost or replacement cost could be implemented here.
            # For MVP, we might update simple unit price if provided.
            if costo_unitario and costo_unitario > 0:
                 # Opcional: Promedio Ponderado, por ahora actualización directa o manual
                 # producto.precio_unitario = costo_unitario 
                 pass
            
        elif tipo == TipoMovimiento.SALIDA.value:
            if producto.stock_actual < cantidad:
                raise ValueError(f"Stock insuficiente. Actual: {producto.stock_actual}")
            producto.stock_actual -= cantidad
            
        else:
            raise ValueError("Tipo de movimiento inválido (ENTRADA/SALIDA).")

        producto.save()

        # TODO: Registrar en tabla Kardex/HistorialMovimientos si se requiere auditoría detallada.

        return {
            "producto_id": producto.id,
            "nuevo_stock": producto.stock_actual,
            "mensaje": f"Movimiento {tipo} exitoso."
        }
