
import pytest
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

@pytest.fixture
def mock_factura_repo():
    return MagicMock()

@pytest.fixture
def mock_pago_repo():
    return MagicMock()

@pytest.fixture
def mock_sri_service():
    return MagicMock()

@pytest.fixture
def mock_email_service():
    return MagicMock()

@pytest.fixture
def use_case(mock_factura_repo, mock_pago_repo, mock_sri_service, mock_email_service):
    return RegistrarCobroUseCase(
        factura_repo=mock_factura_repo,
        pago_repo=mock_pago_repo,
        sri_service=mock_sri_service,
        email_service=mock_email_service
    )

def test_registrar_cobro_exito(use_case, mock_factura_repo, mock_pago_repo, mock_sri_service):
    """
    Escenario: Cobro completo de una factura pendiente.
    Debe:
    1. Calcular totales correctamente.
    2. Cambiar estado a PAGADA.
    3. Registrar pagos en repo.
    4. Generar Clave SRI.
    5. Enviar al SRI.
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
    # Simulamos que tiene el objeto socio cargado (necesario para SRI)
    factura_mock.socio_obj = Socio(id=10, nombres="Juan", apellidos="Perez", cedula="1700000000", email="juan@test.com")
    
    # Mocking Repos
    mock_factura_repo.obtener_por_id.return_value = factura_mock
    mock_pago_repo.tiene_pagos_pendientes.return_value = False # IMPORTANTE: No hay bloqueos
    mock_pago_repo.obtener_sumatoria_validada.return_value = Decimal("0.00")
    
    # Mocking SRI
    mock_sri_service.generar_clave_acceso.return_value = "1234567890123456789012345678901234567890123456789"
    mock_sri_service.enviar_factura.return_value = MagicMock(exito=True, estado='RECIBIDA')

    # Datos de entrada (Cobro Total)
    pagos_input = [{"metodo": "EFECTIVO", "monto": 10.00}]

    # WHEN
    resultado = use_case.ejecutar(factura_id, pagos_input)

    # THEN
    assert resultado['nuevo_estado'] == "PAGADA"
    assert factura_mock.estado == EstadoFactura.PAGADA
    
    # Verificaciones
    mock_pago_repo.registrar_pagos.assert_called_once()
    mock_sri_service.generar_clave_acceso.assert_called_once()
    mock_sri_service.enviar_factura.assert_called_once()
    mock_factura_repo.guardar.assert_called() # Se llama varias veces durante el proceso


def test_registrar_cobro_candado_seguridad(use_case, mock_factura_repo):
    """
    Escenario: Intento de cobro de una factura ya PAGADA.
    Debe:
    1. Lanzar BusinessRuleException (o similar).
    2. No modificar nada.
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
    
    mock_factura_repo.obtener_por_id.return_value = factura_pagada

    # WHEN / THEN
    with pytest.raises(Exception) as excinfo: # Ajustar a Exception específica si se conoce
        use_case.ejecutar(factura_id, [{"metodo": "EFECTIVO", "monto": 10.00}])
    
    # Verificamos que el mensaje mencione que ya está pagada (o similar)
    assert "PAGADA" in str(excinfo.value) or "estado" in str(excinfo.value)