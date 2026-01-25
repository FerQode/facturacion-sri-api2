from core.interfaces.repositories import IMultaRepository
from core.shared.enums import EstadoMulta
from core.shared.exceptions import BusinessRuleException, EntityNotFoundException

class GestionarDisputaMultaUseCase:
    def __init__(self, multa_repo: IMultaRepository):
        self.multa_repo = multa_repo

    def anular_multa(self, multa_id: int, motivo: str):
        """
        Caso A: Pepe demuestra que no cometió la infracción.
        """
        multa = self.multa_repo.get_by_id(multa_id)
        if not multa:
            raise EntityNotFoundException("Multa no encontrada")

        if multa.estado == EstadoMulta.PAGADA:
            raise BusinessRuleException("No se puede anular una multa que ya fue cobrada.")

        # Cambio de estado (Soft Delete)
        multa.estado = EstadoMulta.ANULADA
        multa.observacion = f"{multa.observacion or ''} | [ANULADA]: {motivo}"
        
        # Guardamos cambio
        return self.multa_repo.save(multa)

    def rectificar_monto(self, multa_id: int, nuevo_monto: float, motivo: str):
        """
        Caso B: Pepe solo trabajó medio día ($5 en vez de $10).
        """
        multa = self.multa_repo.get_by_id(multa_id)
        if not multa:
            raise EntityNotFoundException("Multa no encontrada")

        if multa.estado == EstadoMulta.PAGADA:
            raise BusinessRuleException("No se puede editar una multa cobrada.")

        # Lógica de seguridad
        if nuevo_monto < 0:
            raise BusinessRuleException("El monto no puede ser negativo.")

        # Actualizamos valores
        valor_anterior = multa.valor
        multa.valor = nuevo_monto
        multa.observacion = f"{multa.observacion or ''} | [RECTIFICADA]: Valor cambió de ${valor_anterior} a ${nuevo_monto}. Razón: {motivo}"

        return self.multa_repo.save(multa)