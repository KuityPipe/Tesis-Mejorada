"""
Integración de pagos — RF012 del PDF ("Api de pago asociada"). Proveedor
elegido: Transbank Webpay Plus (ver docs/RECOMMENDED_ARCHITECTURE.md §1).

NUEVO en Fase 3, ESQUELETO COMPLETO — no hay credenciales de comercio
Transbank todavía, así que nada de esto puede probarse de punta a punta.
Cuando existan credenciales reales:
  1. `pip install transbank-sdk` (no está en requirements.txt todavía, es
     pesado y no hace falta para levantar el resto del proyecto).
  2. Completar `TRANSBANK_COMMERCE_CODE`/`TRANSBANK_API_KEY` en `.env`.
  3. Reemplazar los `raise NotImplementedError` de abajo por las llamadas
     reales del SDK (`Transaction.create()`/`Transaction.commit()`).
"""
import logging
import environ

env = environ.Env()
logger = logging.getLogger(__name__)


class TransbankService:
    """
    Envoltorio sobre el SDK de Transbank Webpay Plus. Se instancia una vez
    por transacción de pago (ver modelo `Transaccion` en `models.py`, que
    guarda el registro de negocio; esta clase solo habla con la API externa).
    """

    def __init__(self):
        self.commerce_code = env('TRANSBANK_COMMERCE_CODE', default=None)
        self.api_key = env('TRANSBANK_API_KEY', default=None)
        self.ambiente = env('TRANSBANK_ENVIRONMENT', default='integracion')  # 'integracion' o 'produccion'

    def iniciar_transaccion(self, monto, orden_compra, url_retorno):
        """
        TODO: debe llamar a `Transaction.create(orden_compra, session_id, monto, url_retorno)`
        del SDK de Transbank y devolver la URL de pago + el token a la que
        redirigir al usuario. Por ahora solo valida que haya credenciales
        configuradas y avisa que falta implementar la llamada real.
        """
        if not self.commerce_code or not self.api_key:
            logger.warning('TRANSBANK_COMMERCE_CODE/TRANSBANK_API_KEY no configurados en .env — no se puede iniciar el pago')
            raise NotImplementedError(
                'Integración con Transbank pendiente: faltan credenciales de comercio y la llamada real al SDK.'
            )
        raise NotImplementedError('TODO: integrar transbank-sdk Transaction.create()')

    def confirmar_transaccion(self, token):
        """TODO: debe llamar a `Transaction.commit(token)` del SDK y devolver el resultado (aprobado/rechazado)."""
        raise NotImplementedError('TODO: integrar transbank-sdk Transaction.commit()')
