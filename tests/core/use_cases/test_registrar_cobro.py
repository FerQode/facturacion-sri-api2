
import unittest
from unittest.mock import MagicMock, ANY
from decimal import Decimal
from datetime import date, datetime

# Domain
from core.domain.factura import Factura, EstadoFactura
from core.domain.pago import MetodoPagoEnum
from core.domain.socio import Socio
from core.shared.exceptions import BusinessRuleException

# Use Case
from core.use_cases.registrar_cobro_uc import RegistrarCobroUseCase

class TestRegistrarCobro(unittest.TestCase):

    def setUp(self):
        self.mock_factura_repo = MagicMock()
        self.mock_pago_repo = MagicMock()
        self.mock_sri_service = MagicMock()
        self.mock_email_service = MagicMock()

        # Using positional arguments to avoid keyword mismatch issues
        self.use_case = RegistrarCobroUseCase(
            self.mock_factura_repo,
            self.mock_pago_repo,
            self.mock_sri_service,
            self.mock_email_service
        )

    def test_registrar_cobro_exito(self):
        """
        Escenario: Cobro completo de una factura pendiente.
        """
        # GIVEN
        factura_id = 1
            # Use MagicMock here too
        factura_mock = MagicMock(spec=Factura)
        factura_mock.id = factura_id
        factura_mock.socio_id = 10
        factura_mock.medidor_id = 5
        factura_mock.fecha_emision = date(2025, 1, 1)
        factura_mock.fecha_vencimiento = date(2025, 2, 1)
        factura_mock.fecha_registro = datetime(2025, 1, 1, 12, 0, 0)
        factura_mock.total = Decimal("10.00")
        factura_mock.estado = EstadoFactura.PENDIENTE
        factura_mock.detalles = []
        factura_mock.sri_clave_acceso = None # Important for logic
        # Simulamos que tiene el objeto socio cargado
        factura_mock.socio_obj = MagicMock(spec=Socio)
        factura_mock.socio_obj.id = 10
        factura_mock.socio_obj.nombres = "Juan"
        factura_mock.socio_obj.apellidos = "Perez"
        factura_mock.socio_obj.identificacion = "1700000000"
        factura_mock.socio_obj.email = "juan@test.com"
        
        # Mocking Repos
        self.mock_factura_repo.obtener_por_id.return_value = factura_mock
        self.mock_pago_repo.tiene_pagos_pendientes.return_value = False 
        self.mock_pago_repo.obtener_sumatoria_validada.return_value = Decimal("0.00")
        
        # Mocking SRI
        self.mock_sri_service.generar_clave_acceso.return_value = "1234567890123456789012345678901234567890123456789"
        self.mock_sri_service.enviar_factura.return_value = MagicMock(exito=True, estado='RECIBIDA')

        # Datos de entrada
        pagos_input = [{"metodo": "EFECTIVO", "monto": 10.00}]

        # WHEN
        resultado = self.use_case.ejecutar(factura_id, pagos_input)

        # THEN
        self.assertEqual(resultado['nuevo_estado'], "PAGADA")
        self.assertEqual(factura_mock.estado, EstadoFactura.PAGADA)
        
        # Verificaciones
        self.mock_pago_repo.registrar_pagos.assert_called_once()
        self.mock_sri_service.generar_clave_acceso.assert_called_once()
        self.mock_sri_service.enviar_factura.assert_called_once()
        self.mock_factura_repo.guardar.assert_called()

    def test_registrar_cobro_candado_seguridad(self):
        """
        Escenario: Intento de cobro de una factura ya PAGADA.
        """
        # GIVEN
        factura_id = 99
        # Use MagicMock to avoid strict instantiation issues during test
        factura_pagada = MagicMock(spec=Factura)
        factura_pagada.id = factura_id
        factura_pagada.estado = EstadoFactura.PAGADA
        factura_pagada.total = Decimal("10.00")
        
        self.mock_factura_repo.obtener_por_id.return_value = factura_pagada

        # WHEN / THEN
        with self.assertRaises(Exception) as cm:
            self.use_case.ejecutar(factura_id, [{"metodo": "EFECTIVO", "monto": 10.00}])
        
        self.assertIn("PAGADA", str(cm.exception))