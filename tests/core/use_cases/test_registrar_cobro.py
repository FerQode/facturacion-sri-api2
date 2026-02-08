
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
        factura_mock = Factura(
            id=factura_id,
            socio_id=10,
            medidor_id=5,
            fecha_emision=date(2025, 1, 1),
            fecha_vencimiento=date(2025, 2, 1),
            fecha_registro=datetime(2025, 1, 1, 12, 0, 0),
            total=Decimal("10.00"),
            estado=EstadoFactura.PENDIENTE,
            detalles=[]
        )
        # Simulamos que tiene el objeto socio cargado
        factura_mock.socio_obj = Socio(id=10, nombres="Juan", apellidos="Perez", cedula="1700000000", email="juan@test.com")
        
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
        factura_pagada = Factura(
            id=factura_id,
            socio_id=10,
            medidor_id=5,
            fecha_emision=date(2025, 1, 1),
            fecha_vencimiento=date(2025, 2, 1),
            fecha_registro=datetime(2025, 1, 1, 12, 0, 0),
            total=Decimal("10.00"),
            estado=EstadoFactura.PAGADA, # YA PAGADA
            detalles=[]
        )
        
        self.mock_factura_repo.obtener_por_id.return_value = factura_pagada

        # WHEN / THEN
        with self.assertRaises(Exception) as cm:
            self.use_case.ejecutar(factura_id, [{"metodo": "EFECTIVO", "monto": 10.00}])
        
        self.assertIn("PAGADA", str(cm.exception))