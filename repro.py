
from core.domain.factura import Factura, EstadoFactura
from datetime import date, datetime
from decimal import Decimal

try:
    f = Factura(
        id=1,
        socio_id=10,
        medidor_id=5,
        fecha_emision=date(2025, 1, 1),
        fecha_vencimiento=date(2025, 2, 1),
        fecha_registro=datetime(2025, 1, 1, 12, 0, 0),
        total=Decimal("10.00"),
        estado=EstadoFactura.PAGADA,
        detalles=[]
    )
    print("Success")
except Exception as e:
    print(f"Error: {e}")
